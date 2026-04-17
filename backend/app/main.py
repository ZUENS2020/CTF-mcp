from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.callbacks import router as callbacks_router
from app.api.config import router as config_router
from app.api.containers import router as containers_router
from app.config import settings
from app.db.database import init_db
from app.mcp.server import router as mcp_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def _startup() -> None:
        init_db()

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(containers_router)
    app.include_router(config_router)
    app.include_router(callbacks_router)
    app.include_router(mcp_router)

    return app


app = create_app()
