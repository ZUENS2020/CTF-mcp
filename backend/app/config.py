from __future__ import annotations

from threading import RLock
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RuntimeState:
    """In-memory runtime state for active container selection."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._active_container: Optional[str] = None

    def set_active_container(self, name: str) -> None:
        with self._lock:
            self._active_container = name

    def get_active_container(self) -> Optional[str]:
        with self._lock:
            return self._active_container


class AppSettings(BaseSettings):
    app_name: str = "ctf-autopwn"
    app_env: str = "dev"
    docker_base_image: str = "kalilinux/kali-rolling:latest"
    workspace_dir: str = "/tmp/workspace"
    command_timeout_seconds: int = 30
    bore_binary: str = "bore"
    bore_server: str = "bore.pub"
    bore_restart_backoff_seconds: int = 2

    model_config = SettingsConfigDict(env_file=".env", env_prefix="CTF_")


class ConfigUpdate(BaseModel):
    cf_token: Optional[str] = Field(default=None)
    cf_domain: Optional[str] = Field(default=None)


settings = AppSettings()
runtime_state = RuntimeState()
