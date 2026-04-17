from __future__ import annotations

from datetime import datetime
from typing import Dict

from fastapi import APIRouter
from sqlmodel import select

from app.config import ConfigUpdate
from app.db.database import get_session
from app.db.models import ConfigEntry

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("")
def get_config() -> Dict[str, str | None]:
    with get_session() as session:
        items = session.exec(select(ConfigEntry)).all()
    data = {item.key: item.value for item in items}
    return {
        "cf_token": data.get("cf_token"),
        "cf_domain": data.get("cf_domain"),
    }


@router.put("")
def put_config(payload: ConfigUpdate) -> Dict[str, str]:
    updates = {"cf_token": payload.cf_token, "cf_domain": payload.cf_domain}
    with get_session() as session:
        for key, value in updates.items():
            if value is None:
                continue
            entry = session.get(ConfigEntry, key)
            if entry is None:
                entry = ConfigEntry(key=key, value=value)
                session.add(entry)
            else:
                entry.value = value
                entry.updated_at = datetime.utcnow()
                session.add(entry)
        session.commit()
    return {"message": "config updated"}
