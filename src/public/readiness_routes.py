from __future__ import annotations

from html import escape
from pathlib import Path
from urllib.parse import urljoin

from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse, PlainTextResponse, Response
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.core.config import Settings, get_settings
from src.public.content_service import get_page_by_key, list_legal_pages, list_navigation, list_platforms

router = APIRouter()
PUBLIC_DIR = Path(__file__).resolve().parent
BRAND_DIR = PUBLIC_DIR / "static" / "img" / "brand"


def _absolute(settings: Settings, path: str) -> str:
    base = settings.public_base_url.rstrip("/") + "/"
    return urljoin(base, path.lstrip("/"))


def _published_routes(db: Session, locale: str) -> list[str]:
    routes: set[str] = set()
    home = get_page_by_key(db, page_key="home", locale=locale, include_drafts=False)
    if home is not None:
        routes.add("/en/" if locale == "en" else "/")
    for item in list_navigation(db, locale=locale, include_drafts=False):
        routes.add(item.route_path)
    for item in list_platforms(db, locale=locale, include_drafts=False):
        routes.add(item.route_path)
    for item in list_legal_pages(db, locale=locale):
        routes.add(item.route_path)
    return sorted(routes)


@router.get("/robots.txt", include_in_schema=False)
def robots_txt(settings: Settings = Depends(get_settings)) -> PlainTextResponse:
    if settings.isi_env.casefold() != "production":
        body = "User-agent: *\nDisallow: /\n"
    else:
        body = (
            "User-agent: *\n"
            "Allow: /\n"
            "Disallow: /app\n"
            "Disallow: /api/\n"
            f"Sitemap: {_absolute(settings, '/sitemap.xml')}\n"
        )
    return PlainTextResponse(body, media_type="text/plain")


@router.get("/sitemap.xml", include_in_schema=False)
def sitemap_xml(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Response:
    routes = set(_published_routes(db, "sr-Latn")) | set(_published_routes(db, "en"))
    urls = "".join(
        f"<url><loc>{escape(_absolute(settings, route))}</loc></url>" for route in sorted(routes)
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{urls}</urlset>"
    )
    return Response(content=xml, media_type="application/xml")


@router.get("/site.webmanifest", include_in_schema=False)
def site_manifest(settings: Settings = Depends(get_settings)) -> Response:
    payload = (
        '{'
        '"name":"Institut za socijalnu inkluziju",'
        '"short_name":"ISI",'
        '"start_url":"/",'
        '"scope":"/",'
        '"display":"standalone",'
        '"background_color":"#f5f0e6",'
        '"theme_color":"#103d34",'
        '"icons":[{'
        '"src":"/static/img/brand/isi-logo-transparent.svg",'
        '"sizes":"any",'
        '"type":"image/svg+xml",'
        '"purpose":"any"'
        '}]'
        '}'
    )
    return Response(content=payload, media_type="application/manifest+json")


@router.get("/favicon.ico", include_in_schema=False)
def favicon() -> FileResponse:
    path = BRAND_DIR / "isi-logo-transparent.svg"
    return FileResponse(path, media_type="image/svg+xml")
