from __future__ import annotations

import argparse
import base64
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class Context:
    base_url: str
    container_name: str
    image: str
    bore_port: int
    callback_token: str
    require_bore: bool
    keep_container: bool


class StepError(RuntimeError):
    pass


def log(msg: str) -> None:
    print(f"[E2E] {msg}")


def http_json(ctx: Context, method: str, path: str, payload: dict | None = None) -> dict | list:
    url = f"{ctx.base_url}{path}"
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url=url, method=method.upper(), data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            if not body:
                return {}
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise StepError(f"{method} {path} failed: HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise StepError(f"{method} {path} failed: {exc}") from exc


def http_text(ctx: Context, method: str, path: str, body: str, content_type: str = "text/plain") -> str:
    url = f"{ctx.base_url}{path}"
    req = urllib.request.Request(
        url=url,
        method=method.upper(),
        data=body.encode("utf-8"),
        headers={"Content-Type": content_type},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise StepError(f"{method} {path} failed: HTTP {exc.code}: {detail}") from exc


def ensure(cond: bool, message: str) -> None:
    if not cond:
        raise StepError(message)


def run(ctx: Context) -> None:
    log(f"base={ctx.base_url} container={ctx.container_name}")

    log("1/11 health check")
    health = http_json(ctx, "GET", "/healthz")
    ensure(isinstance(health, dict) and health.get("status") == "ok", "healthz returned unexpected payload")

    log("2/11 create container")
    http_json(ctx, "POST", "/api/containers", {"name": ctx.container_name, "image": ctx.image})

    log("3/11 set active container")
    active = http_json(ctx, "PUT", f"/api/containers/{urllib.parse.quote(ctx.container_name)}/activate")
    ensure(isinstance(active, dict) and active.get("name") == ctx.container_name, "activate response mismatch")

    log("4/11 MCP shell_exec sanity")
    shell_res = http_json(
        ctx,
        "POST",
        "/mcp",
        {"tool": "shell_exec", "arguments": {"cmd": "echo phase06_ok"}},
    )
    out = ((shell_res or {}).get("result") or {}).get("output", "") if isinstance(shell_res, dict) else ""
    ensure("phase06_ok" in out, "shell_exec output missing marker")

    log("5/11 upload/read file through MCP")
    http_json(
        ctx,
        "POST",
        "/mcp",
        {"tool": "shell_exec", "arguments": {"cmd": "mkdir -p /tmp/workspace"}},
    )

    sample = f"phase06-file-check @ {datetime.now(timezone.utc).isoformat()}"
    encoded = base64.b64encode(sample.encode("utf-8")).decode("ascii")
    http_json(
        ctx,
        "POST",
        "/mcp",
        {"tool": "upload_file", "arguments": {"name": "phase06.txt", "b64": encoded}},
    )
    read_res = http_json(
        ctx,
        "POST",
        "/mcp",
        {"tool": "read_file", "arguments": {"path": "phase06.txt"}},
    )
    content = ((read_res or {}).get("result") or {}).get("content", "") if isinstance(read_res, dict) else ""
    ensure(sample == content, "read_file content mismatch")

    log("6/11 post callback")
    marker = f"phase06-callback-{int(time.time())}"
    http_text(ctx, "POST", f"/callback/{ctx.callback_token}", marker)

    log("7/11 MCP get_callbacks validation")
    callbacks_res = http_json(
        ctx,
        "POST",
        "/mcp",
        {
            "tool": "get_callbacks",
            "arguments": {
                "since": (datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")),
                "limit": 50,
            },
        },
    )

    # Since is "now", include fallback query for recent rows.
    found = False
    items = []
    if isinstance(callbacks_res, dict):
        items = ((callbacks_res.get("result") or {}).get("items") or [])
        for row in items:
            if row.get("token") == ctx.callback_token and marker in row.get("body", ""):
                found = True
                break

    if not found:
        callbacks_res = http_json(ctx, "POST", "/mcp", {"tool": "get_callbacks", "arguments": {"limit": 100}})
        items = ((callbacks_res.get("result") or {}).get("items") or []) if isinstance(callbacks_res, dict) else []
        for row in items:
            if row.get("token") == ctx.callback_token and marker in row.get("body", ""):
                found = True
                break

    ensure(found, "get_callbacks did not return posted callback")

    log("8/11 list_bore_tunnels")
    list_before = http_json(ctx, "POST", "/mcp", {"tool": "list_bore_tunnels", "arguments": {}})
    ensure(isinstance(list_before, dict), "list_bore_tunnels response invalid")

    log("9/11 start_bore")
    bore_error = None
    try:
        started = http_json(
            ctx,
            "POST",
            "/mcp",
            {"tool": "start_bore", "arguments": {"local_port": ctx.bore_port}},
        )
        ensure(isinstance(started, dict), "start_bore response invalid")
    except StepError as exc:
        bore_error = str(exc)
        if ctx.require_bore:
            raise

    if bore_error:
        log(f"WARN bore start skipped: {bore_error}")
    else:
        log("10/11 stop_bore")
        time.sleep(1)
        http_json(
            ctx,
            "POST",
            "/mcp",
            {"tool": "stop_bore", "arguments": {"local_port": ctx.bore_port}},
        )

    log("11/11 teardown")
    if not ctx.keep_container:
        http_json(ctx, "DELETE", f"/api/containers/{urllib.parse.quote(ctx.container_name)}")


def parse_args() -> Context:
    parser = argparse.ArgumentParser(description="Phase 06 E2E validation script")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--container", default=f"phase06-kali-{int(time.time())}")
    parser.add_argument("--image", default="kalilinux/kali-rolling:latest")
    parser.add_argument("--bore-port", type=int, default=4444)
    parser.add_argument("--callback-token", default=f"phase06-token-{int(time.time())}")
    parser.add_argument("--require-bore", action="store_true")
    parser.add_argument("--keep-container", action="store_true")
    ns = parser.parse_args()

    return Context(
        base_url=ns.base_url.rstrip("/"),
        container_name=ns.container,
        image=ns.image,
        bore_port=ns.bore_port,
        callback_token=ns.callback_token,
        require_bore=ns.require_bore,
        keep_container=ns.keep_container,
    )


def main() -> int:
    ctx = parse_args()
    try:
        run(ctx)
    except StepError as exc:
        log(f"FAILED: {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - top-level guard
        log(f"FAILED (unexpected): {exc}")
        return 1

    log("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
