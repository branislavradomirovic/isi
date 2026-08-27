from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


def register_public_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def public_http_exception_handler(request: Request, exc: StarletteHTTPException):
        path = request.url.path
        if path.startswith("/api/"):
            return JSONResponse({"detail": exc.detail}, status_code=exc.status_code, headers=exc.headers)
        if exc.status_code != 404:
            return JSONResponse({"detail": exc.detail}, status_code=exc.status_code, headers=exc.headers)
        locale = "en" if path == "/en" or path.startswith("/en/") else "sr-Latn"
        return templates.TemplateResponse(
            request=request,
            name="errors/404.html",
            status_code=404,
            context={"locale": locale, "requested_path": path},
        )
