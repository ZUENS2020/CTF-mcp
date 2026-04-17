from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlmodel import select

from app.db.database import get_session
from app.db.models import CallbackRecord

from .shell import ToolError


def _parse_since(since: Optional[str]) -> Optional[datetime]:
    if since is None:
        return None
    raw = since.strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ToolError("since must be ISO datetime, e.g. 2026-04-17T12:00:00Z") from exc


def get_callbacks(since: str | None = None, limit: int = 100) -> Dict[str, Any]:
    if limit < 1 or limit > 1000:
        raise ToolError("limit must be between 1 and 1000")
    since_dt = _parse_since(since)

    with get_session() as session:
        stmt = select(CallbackRecord).order_by(CallbackRecord.created_at.desc()).limit(limit)
        if since_dt is not None:
            stmt = stmt.where(CallbackRecord.created_at >= since_dt)
        rows = session.exec(stmt).all()

    return {
        "count": len(rows),
        "items": [
            {
                "id": row.id,
                "token": row.token,
                "source_ip": row.source_ip,
                "headers_json": row.headers_json,
                "body": row.body,
                "created_at": row.created_at.isoformat() + "Z",
            }
            for row in rows
        ],
    }
