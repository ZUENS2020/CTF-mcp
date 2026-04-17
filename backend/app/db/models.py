from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class CallbackRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    token: str = Field(index=True)
    source_ip: Optional[str] = None
    headers_json: str
    body: str
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class ConfigEntry(SQLModel, table=True):
    key: str = Field(primary_key=True)
    value: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)
