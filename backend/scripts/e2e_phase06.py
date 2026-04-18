"""End-to-end validation for pure API backend (no MCP endpoint)."""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass


@dataclass
class Context:
    base_url: str
    container_name: str
    image: str
    callback_token: str
    keep_container: bool


class StepError(RuntimeError):
    pass


def log(msg: str) -> None:
    print(f"[E2E] {msg}")


def http_json(ctx: Context, method: str, path: str, payload: dict | None = None) -> dict | list:
    url = f"{ctx.base_url}{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url=url,
        method=method.upper(),
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise StepError(f"{method} {path} -> HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise StepError(f"{method} {path} -> {exc}") from exc


def http_text(ctx: Context, method: str, path: str, body: str) -> str:
    url = f"{ctx.base_url}{path}"
    req = urllib.request.Request(
        url=url,
        method=method.upper(),
        data=body.encode(),
        headers={"Content-Type": "text/plain"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode(errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise StepError(f"{method} {path} -> HTTP {exc.code}: {detail}") from exc


def ensure(cond: bool, message: str) -> None:
    if not cond:
        raise StepError(message)


def run(ctx: Context) -> None:
    log(f"base={ctx.base_url} container={ctx.container_name}")
    container_created = False

    try:
        log("1/7 health check")
        health = http_json(ctx, "GET", "/healthz")
        ensure(isinstance(health, dict) and health.get("status") == "ok", "healthz unexpected payload")

        log("2/7 create container")
        http_json(ctx, "POST", "/api/containers", {"name": ctx.container_name, "image": ctx.image})
        container_created = True

        log("3/7 kali exec sanity")
        exec_res = http_json(
            ctx,
            "POST",
            "/api/kali/exec",
            {"container": ctx.container_name, "cmd": "echo phase06_ok"},
        )
        ensure("phase06_ok" in str(exec_res.get("output", "")), "kali exec output missing marker")

        log("4/7 kali read")
        sample = f"phase06_file_check_{int(time.time())}"
        http_json(
            ctx,
            "POST",
            "/api/kali/exec",
            {
                "container": ctx.container_name,
                "cmd": f"mkdir -p /tmp/workspace && echo {sample} > /tmp/workspace/phase06.txt",
            },
        )
        read_res = http_json(ctx, "POST", "/api/kali/read", {"container": ctx.container_name, "path": "phase06.txt"})
        ensure(read_res.get("content", "").strip() == sample, "kali read content mismatch")

        log("5/7 post callback")
        marker = f"phase06-callback-{int(time.time())}"
        http_text(ctx, "POST", f"/callback/{ctx.callback_token}", marker)

        log("6/7 list callbacks")
        callbacks = http_json(ctx, "GET", "/api/callbacks")
        ensure(
            any(row.get("token") == ctx.callback_token and marker in row.get("body", "") for row in callbacks),
            "callback not found",
        )

    finally:
        log("7/7 teardown")
        if container_created and not ctx.keep_container:
            try:
                http_json(ctx, "DELETE", f"/api/containers/{urllib.parse.quote(ctx.container_name)}")
            except StepError as exc:
                log(f"WARN teardown failed: {exc}")


def parse_args() -> Context:
    parser = argparse.ArgumentParser(description="Phase 06 E2E validation script (pure API)")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--container", default=f"phase06-kali-{int(time.time())}")
    parser.add_argument("--image", default="kalilinux/kali-rolling:latest")
    parser.add_argument("--callback-token", default=f"phase06-token-{int(time.time())}")
    parser.add_argument("--keep-container", action="store_true", help="do not delete container after test")
    ns = parser.parse_args()
    return Context(
        base_url=ns.base_url.rstrip("/"),
        container_name=ns.container,
        image=ns.image,
        callback_token=ns.callback_token,
        keep_container=ns.keep_container,
    )


def main() -> int:
    ctx = parse_args()
    try:
        run(ctx)
    except StepError as exc:
        log(f"FAILED: {exc}")
        return 1
    except Exception as exc:
        log(f"FAILED (unexpected): {exc}")
        return 1
    log("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
