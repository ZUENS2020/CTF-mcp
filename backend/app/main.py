from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.callbacks import router as callbacks_router
from app.api.config import router as config_router
from app.api.containers import router as containers_router
from app.config import settings
from app.db.database import init_db
from app.mcp.server import mcp


def create_app() -> FastAPI:
    mcp_app = mcp.http_app()
    app = FastAPI(title=settings.app_name, lifespan=mcp_app.lifespan)

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
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(containers_router)
    app.include_router(config_router)
    app.include_router(callbacks_router)

    # Mount standard MCP Streamable HTTP transport at /mcp
    # FastMCP serves at /mcp internally; mounting at "/" keeps the endpoint at /mcp
    # while FastAPI explicit routes (/api/*, /healthz) retain priority.
    app.mount("/", mcp_app)

    return app


app = create_app()
