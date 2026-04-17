"""
End-to-end validation script for CTF AutoPwn.

Tests REST endpoints (containers, callbacks, config) and all MCP tools via
the standard MCP Streamable HTTP transport (JSON-RPC 2.0).
"""
from __future__ import annotations

import argparse
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
    callback_token: str
    keep_container: bool


class StepError(RuntimeError):
    pass


def log(msg: str) -> None:
    print(f"[E2E] {msg}")


# ---------------------------------------------------------------------------
# REST helpers
# ---------------------------------------------------------------------------

def http_json(ctx: Context, method: str, path: str, payload: dict | None = None) -> dict | list:
    url = f"{ctx.base_url}{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url=url, method=method.upper(), data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise StepError(f"{method} {path} → HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise StepError(f"{method} {path} → {exc}") from exc


def http_text(ctx: Context, method: str, path: str, body: str) -> str:
    url = f"{ctx.base_url}{path}"
    req = urllib.request.Request(
        url=url, method=method.upper(),
        data=body.encode(),
        headers={"Content-Type": "text/plain"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode(errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise StepError(f"{method} {path} → HTTP {exc.code}: {detail}") from exc


def ensure(cond: bool, message: str) -> None:
    if not cond:
        raise StepError(message)


# ---------------------------------------------------------------------------
# MCP client — standard Streamable HTTP transport (JSON-RPC 2.0)
# ---------------------------------------------------------------------------

class MCPClient:
    """Minimal stateless MCP client over HTTP."""

    def __init__(self, base_url: str) -> None:
        self._url = base_url.rstrip("/") + "/mcp"
        self._session_id: str | None = None
        self._req_id = 0

    def _next_id(self) -> int:
        self._req_id += 1
        return self._req_id

    @staticmethod
    def _parse_sse_json(body: str) -> dict:
        """Extract the first valid JSON payload from an SSE response body."""
        payloads: list[str] = []
        current_data: list[str] = []

        for raw_line in body.splitlines():
            line = raw_line.rstrip("\r")
            if not line:
                if current_data:
                    payloads.append("\n".join(current_data).strip())
                    current_data = []
                continue
            if line.startswith("data:"):
                current_data.append(line[5:].lstrip())

        if current_data:
            payloads.append("\n".join(current_data).strip())

        for payload in payloads:
            if not payload:
                continue
            try:
                return json.loads(payload)
            except json.JSONDecodeError:
                continue

        preview = payloads[0] if payloads else "<no-data-lines>"
        raise StepError(f"MCP SSE response contains no JSON payload: {preview}")

    def _post(self, payload: dict) -> dict:
        data = json.dumps(payload).encode()
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id
        req = urllib.request.Request(url=self._url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                # Capture session ID from response headers
                sid = resp.headers.get("Mcp-Session-Id")
                if sid:
                    self._session_id = sid
                body = resp.read().decode()
                if not body.strip():
                    return {}
                content_type = (resp.headers.get("Content-Type") or "").lower()
                if "text/event-stream" in content_type or "data:" in body or "event:" in body:
                    return self._parse_sse_json(body)
                return json.loads(body)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            raise StepError(f"MCP POST → HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise StepError(f"MCP POST → {exc}") from exc

    def initialize(self) -> None:
        resp = self._post({
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "e2e-test", "version": "1.0"},
            },
        })
        if "error" in resp:
            raise StepError(f"MCP initialize failed: {resp['error']}")
        # Send initialized notification (no response expected)
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def list_tools(self) -> list[dict]:
        resp = self._post({
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/list",
        })
        if "error" in resp:
            raise StepError(f"MCP tools/list failed: {resp['error']}")
        return resp.get("result", {}).get("tools", [])

    def call_tool(self, name: str, arguments: dict) -> dict:
        resp = self._post({
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        })
        if "error" in resp:
            raise StepError(f"MCP tools/call {name} failed: {resp['error']}")
        result = resp.get("result", {})
        # FastMCP returns content as list of text blocks; unwrap to dict for convenience
        content = result.get("content", [])
        if content and isinstance(content, list) and content[0].get("type") == "text":
            try:
                return json.loads(content[0]["text"])
            except (json.JSONDecodeError, KeyError):
                return {"raw": content[0].get("text", "")}
        return result


# ---------------------------------------------------------------------------
# Test steps
# ---------------------------------------------------------------------------

def run(ctx: Context) -> None:
    log(f"base={ctx.base_url} container={ctx.container_name}")
    container_created = False

    try:
        # 1. Health check
        log("1/11 health check")
        health = http_json(ctx, "GET", "/healthz")
        ensure(isinstance(health, dict) and health.get("status") == "ok", "healthz unexpected payload")

        # 2. Create container
        log("2/11 create container")
        http_json(ctx, "POST", "/api/containers", {"name": ctx.container_name, "image": ctx.image})
        container_created = True

        # 3. Activate container
        log("3/11 activate container")
        active = http_json(ctx, "PUT", f"/api/containers/{urllib.parse.quote(ctx.container_name)}/activate")
        ensure(isinstance(active, dict) and active.get("name") == ctx.container_name, "activate response mismatch")

        # Initialise MCP session
        mcp = MCPClient(ctx.base_url)
        mcp.initialize()

        # Verify tools are registered
        tools = mcp.list_tools()
        tool_names = {t["name"] for t in tools}
        for expected in ("shell_exec", "read_file", "get_callbacks"):
            ensure(expected in tool_names, f"MCP tool '{expected}' not found in tools/list")

        # 4. shell_exec
        log("4/11 MCP shell_exec")
        shell_res = mcp.call_tool("shell_exec", {"cmd": "echo phase06_ok"})
        ensure("phase06_ok" in shell_res.get("output", ""), "shell_exec output missing marker")

        # 5. shell_exec write + read_file
        log("5/11 MCP shell_exec write / read_file")
        mcp.call_tool("shell_exec", {"cmd": "mkdir -p /tmp/workspace"})
        sample = f"phase06_file_check_{int(time.time())}"
        mcp.call_tool("shell_exec", {"cmd": f"echo {sample} > /tmp/workspace/phase06.txt"})
        read_res = mcp.call_tool("read_file", {"path": "phase06.txt"})
        ensure(read_res.get("content", "").strip() == sample, "read_file content mismatch")

        # 6. Post callback via REST
        log("6/11 post callback")
        marker = f"phase06-callback-{int(time.time())}"
        http_text(ctx, "POST", f"/callback/{ctx.callback_token}", marker)

        # 7. get_callbacks via MCP
        log("7/11 MCP get_callbacks")
        cb_res = mcp.call_tool("get_callbacks", {"limit": 100})
        found = any(
            r.get("token") == ctx.callback_token and marker in r.get("body", "")
            for r in cb_res.get("items", [])
        )
        ensure(found, "get_callbacks did not return posted callback")

    finally:
        # 8. Teardown
        log("8/8 teardown")
        if container_created and not ctx.keep_container:
            try:
                http_json(ctx, "DELETE", f"/api/containers/{urllib.parse.quote(ctx.container_name)}")
            except StepError as exc:
                log(f"WARN teardown failed: {exc}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> Context:
    parser = argparse.ArgumentParser(description="Phase 06 E2E validation script")
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
