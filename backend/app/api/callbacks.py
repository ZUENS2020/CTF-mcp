from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, Request
from sqlmodel import delete, select

from app.db.database import get_session
from app.db.models import CallbackRecord

router = APIRouter(tags=["callbacks"])


@router.get("/api/callbacks")
def list_callbacks(since: Optional[datetime] = None) -> list[CallbackRecord]:
    with get_session() as session:
        stmt = select(CallbackRecord).order_by(CallbackRecord.created_at.desc())
        if since is not None:
            stmt = stmt.where(CallbackRecord.created_at >= since)
        return session.exec(stmt).all()


@router.delete("/api/callbacks")
def clear_callbacks() -> Dict[str, str]:
    with get_session() as session:
        session.exec(delete(CallbackRecord))
        session.commit()
    return {"message": "callbacks cleared"}


@router.post("/callback/{token}")
async def receive_callback(token: str, request: Request) -> Dict[str, str]:
    body = await request.body()
    headers = dict(request.headers)

    record = CallbackRecord(
        token=token,
        source_ip=request.client.host if request.client else None,
        headers_json=json.dumps(headers, ensure_ascii=False),
        body=body.decode("utf-8", errors="replace"),
    )

    with get_session() as session:
        session.add(record)
        session.commit()

    return {"message": "received"}
