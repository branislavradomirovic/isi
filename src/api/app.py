from src.platform.deployment.runtime import validate_deployment_runtime_settings
from src.api.deployment_routes import router as deployment_router
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from src.api.auth_routes import router as auth_router
from src.api.app_context_routes import router as app_context_router
from src.api.app_shell_routes import router as app_shell_router
from src.api.data_routes import router as data_router
from src.api.ai_routes import router as ai_router
from src.api.simpa_routes import router as simpa_router
from src.api.simpa_analytics_routes import router as simpa_analytics_router
from src.api.ordo_routes import router as ordo_router
from src.api.ordo_analytics_routes import router as ordo_analytics_router
from src.api.reporting_routes import router as reporting_router
from src.api.administration_routes import router as administration_router
from src.core.config import get_settings
from src.core.logging import configure_logging
from src.platform.security.middleware import SecurityHeadersMiddleware
from src.platform.security.service import parse_allowed_hosts, validate_production_security_settings
from src.public.routes import router as public_router
from src.public.error_handlers import register_public_error_handlers

configure_logging()
# ISI-14 application security baseline
_security_settings = get_settings()
validate_production_security_settings(_security_settings)
validate_deployment_runtime_settings(_security_settings)
app = FastAPI(title="ISI Platform API", version="0.1.0")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=parse_allowed_hosts(_security_settings.security_allowed_hosts))
app.add_middleware(SecurityHeadersMiddleware, environment=_security_settings.isi_env)

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
app.include_router(simpa_analytics_router)
app.include_router(ordo_router)
app.include_router(ordo_analytics_router)
app.include_router(reporting_router)
app.include_router(administration_router)
app.include_router(deployment_router)


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "isi-api", "phase": "foundation"}
