from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.api.auth_routes import router as auth_router
from src.api.app_context_routes import router as app_context_router
from src.api.app_shell_routes import router as app_shell_router
from src.api.data_routes import router as data_router
from src.api.ai_routes import router as ai_router
from src.api.simpa_routes import router as simpa_router
from src.core.logging import configure_logging
from src.public.routes import router as public_router
from src.public.error_handlers import register_public_error_handlers

configure_logging()
app = FastAPI(title="ISI Platform API", version="0.1.0")

PUBLIC_DIR = Path(__file__).resolve().parents[1] / "public"
app.mount("/static", StaticFiles(directory=str(PUBLIC_DIR / "static")), name="static")
app.mount("/media", StaticFiles(directory="var/media/public", check_dir=False), name="media")
app.include_router(public_router)
register_public_error_handlers(app)
app.include_router(auth_router)
app.include_router(app_context_router)
app.include_router(app_shell_router)
app.include_router(data_router)
app.include_router(ai_router)
app.include_router(simpa_router)


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "isi-api", "phase": "foundation"}
