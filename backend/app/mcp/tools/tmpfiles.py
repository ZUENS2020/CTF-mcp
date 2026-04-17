from __future__ import annotations

import json
import mimetypes
import os
import posixpath
import re
import urllib.parse
import urllib.request
from typing import Any, Dict

from app.config import settings
from app.core.docker import get_docker_service
from app.core.errors import ToolError

from .shell import _active_container, _run_docker_call, _safe_workspace_path


def _build_multipart(field_name: str, filename: str, data: bytes) -> tuple[bytes, str]:
    boundary = f"----ctf-tmpfiles-{os.urandom(8).hex()}"
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    body = bytearray()
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(
        (
            f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode()
    )
    body.extend(data)
    body.extend(f"\r\n--{boundary}--\r\n".encode())

    return bytes(body), f"multipart/form-data; boundary={boundary}"


def _extract_public_url(payload: dict[str, Any]) -> str:
    data = payload.get("data")
    if isinstance(data, dict):
        for key in ("url", "download_url", "link"):
            value = data.get(key)
            if isinstance(value, str) and value.startswith("http"):
                return value
    for key in ("url", "download_url", "link"):
        value = payload.get(key)
        if isinstance(value, str) and value.startswith("http"):
            return value
    raise ToolError(f"tmpfiles upload response missing url: {payload}")


def _to_download_url(url_or_id: str) -> str:
    raw = url_or_id.strip()
    if not raw:
        raise ToolError("url_or_id is required")

    if re.fullmatch(r"\d+", raw):
        return f"{settings.tmpfiles_api_base.rstrip('/')}/dl/{raw}"

    if not raw.startswith("http://") and not raw.startswith("https://"):
        raise ToolError("url_or_id must be tmpfiles URL or numeric id")

    parsed = urllib.parse.urlparse(raw)
    if "tmpfiles.org" not in parsed.netloc:
        raise ToolError("only tmpfiles.org URLs are supported")

    if parsed.path.startswith("/dl/"):
        return raw

    path = parsed.path
    if not path or path == "/":
        raise ToolError("invalid tmpfiles URL")

    if not path.startswith("/dl/"):
        path = "/dl" + (path if path.startswith("/") else f"/{path}")

    rebuilt = parsed._replace(path=path)
    return urllib.parse.urlunparse(rebuilt)


def _filename_from_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    name = posixpath.basename(parsed.path.rstrip("/"))
    if not name:
        return "tmpfiles_download.bin"
    return name


async def tmpfiles_upload(path: str) -> Dict[str, Any]:
    """Upload a file from active container workspace to tmpfiles.org. path is relative to /tmp/workspace/."""
    active = _active_container()
    target = _safe_workspace_path(path)

    file_bytes = await _run_docker_call(get_docker_service().read_file_bytes, active, target)
    if file_bytes == b"":
        raise ToolError(f"file is empty or not found: {target}")

    filename = posixpath.basename(target)
    body, content_type = _build_multipart("file", filename, file_bytes)

    upload_url = f"{settings.tmpfiles_api_base.rstrip('/')}/api/v1/upload"
    request = urllib.request.Request(
        upload_url,
        method="POST",
        data=body,
        headers={
            "Content-Type": content_type,
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=settings.tmpfiles_http_timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8", errors="replace"))
    except Exception as exc:
        raise ToolError(f"tmpfiles upload failed: {exc}") from exc

    url = _extract_public_url(payload)
    return {
        "path": target,
        "size": len(file_bytes),
        "url": url,
        "download_url": _to_download_url(url),
        "container": active,
    }


async def tmpfiles_download(url_or_id: str, save_as: str | None = None) -> Dict[str, Any]:
    """Download a tmpfiles.org file to active container workspace. save_as is optional relative path under /tmp/workspace/."""
    active = _active_container()
    download_url = _to_download_url(url_or_id)

    try:
        with urllib.request.urlopen(download_url, timeout=settings.tmpfiles_http_timeout_seconds) as response:
            payload = response.read()
            final_url = response.geturl()
    except Exception as exc:
        raise ToolError(f"tmpfiles download failed: {exc}") from exc

    if not payload:
        raise ToolError("tmpfiles download returned empty payload")

    name = save_as or _filename_from_url(final_url)
    target = _safe_workspace_path(name)

    await _run_docker_call(get_docker_service().write_file, active, target, payload)
    return {
        "path": target,
        "size": len(payload),
        "source": download_url,
        "resolved_url": final_url,
        "container": active,
    }
