from __future__ import annotations

from typing import Iterable

from app.core.errors import ToolError

BLOCKED_TOKENS = {
    "rm -rf /",
    "docker",
    "shutdown",
    "reboot",
    "mkfs",
}


def validate_command(cmd: str, blacklist: Iterable[str] = BLOCKED_TOKENS) -> None:
    normalized = cmd.strip().lower()
    for item in blacklist:
        if item in normalized:
            raise ToolError(f"blocked command token: {item}")
