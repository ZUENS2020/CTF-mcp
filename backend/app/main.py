from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.callbacks import router as callbacks_router
from app.api.config import router as config_router
from app.api.containers import router as containers_router
from app.api.kali import router as kali_router
from app.config import settings
from app.db.database import init_db


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    # Create database tables during app construction. FastAPI startup hooks are
    # replaced when a custom lifespan is provided.
    init_db()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(containers_router)
    app.include_router(kali_router)
    app.include_router(config_router)
    app.include_router(callbacks_router)

    return app


app = create_app()
