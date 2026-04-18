from __future__ import annotations

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppSettings(BaseSettings):
    app_name: str = "ctf-autopwn"
    app_env: str = "dev"
    docker_base_image: str = "ctf-kali:latest"
    container_platform: Optional[str] = "linux/amd64"
    workspace_dir: str = "/tmp/workspace"
    command_timeout_seconds: int = 30
    container_mem_limit: str = "32g"
    container_nano_cpus: int = 8_000_000_000
    container_pids_limit: int = 32768
    container_shm_size: str = "8g"
    docker_api_timeout_seconds: int = 15
    docker_operation_timeout_seconds: int = 20
    tmpfiles_api_base: str = "https://tmpfiles.org"
    tmpfiles_http_timeout_seconds: int = 30

    model_config = SettingsConfigDict(env_file=".env", env_prefix="CTF_")


class ConfigUpdate(BaseModel):
    cf_token: Optional[str] = Field(default=None)
    cf_domain: Optional[str] = Field(default=None)


settings = AppSettings()
