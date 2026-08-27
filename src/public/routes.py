from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.core.config import Settings, get_settings
from src.public.catalog_service import activity_catalog_from_html, document_catalog_from_html, library_catalog_from_html
from src.public.content_service import (
    PublicPageView,
    alternate_locale_page,
    get_page_by_key,
    get_page_by_route,
    list_navigation,
    list_platforms,
)
from src.public.readiness_routes import router as readiness_router
from src.public.section_service import list_page_sections
from src.public.semantic_icons import activity_icon, document_icon, semantic_icon

ROUTER_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(ROUTER_DIR / "templates"))
templates.env.globals.update(
    semantic_icon=semantic_icon,
    document_icon=document_icon,
    activity_icon=activity_icon,
)
router = APIRouter()

RETIRED_PUBLIC_TOKENS = (
    "ancsee",
    "academic network for cooperation",
    "wbsib",
    "western balkan social inclusion barometer",
)


def preview_enabled(settings: Settings) -> bool:
    return bool(settings.public_preview_drafts and settings.isi_env.casefold() != "production")


def canonical_route(page: PublicPageView) -> str:
    if page.page_key == "home":
        return "/en/" if page.locale == "en" else "/"
    return page.route_path


def _not_retired(item: PublicPageView) -> bool:
    haystack = f"{item.page_key} {item.title} {item.route_path}".casefold()
    return not any(token in haystack for token in RETIRED_PUBLIC_TOKENS)


def _common_context(
    request: Request,
    *,
    db: Session,
    settings: Settings,
    locale: str,
    page: PublicPageView,
) -> dict[str, object]:
    include_drafts = preview_enabled(settings)
    other_locale = "en" if locale == "sr-Latn" else "sr-Latn"
    alternate = alternate_locale_page(
        db,
        page_key=page.page_key,
        locale=other_locale,
        include_drafts=include_drafts,
    )
    navigation = [item for item in list_navigation(db, locale=locale, include_drafts=include_drafts) if _not_retired(item)]
    platforms = list_platforms(db, locale=locale, include_drafts=include_drafts)
    base_url = settings.public_base_url.rstrip("/")
    canonical = base_url + canonical_route(page)
    alternate_url = (base_url + canonical_route(alternate)) if alternate else None
    if locale == "sr-Latn":
        x_default_path = canonical
    elif alternate is not None:
        x_default_path = base_url + canonical_route(alternate)
    else:
        x_default_path = base_url + "/"
    return {
        "request": request,
        "page": page,
        "title": page.seo_title or page.title,
        "meta_description": page.meta_description or page.excerpt,
        "locale": locale,
        "lang_code": "en" if locale == "en" else "sr-Latn",
        "navigation": navigation,
        "platforms": platforms,
        "canonical_path": canonical,
        "alternate_path": alternate_url,
        "alternate_label": "SR" if locale == "en" else "EN",
        "x_default_path": x_default_path,
        "og_locale": "en_US" if locale == "en" else "sr_RS",
        "og_locale_alternate": "sr_RS" if locale == "en" and alternate else ("en_US" if alternate else None),
        "robots_directive": "noindex,nofollow" if settings.isi_env.casefold() != "production" or include_drafts else "index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1",
        "share_image_url": base_url + "/static/img/brand/isi-logo-transparent.svg",
        "app_url": settings.app_base_url,
        "preview_mode": include_drafts,
        "sections": list_page_sections(db, page_id=page.page_id, locale=locale, include_drafts=include_drafts),
    }


def _preview_catalogs(db: Session, *, locale: str, include_drafts: bool) -> tuple[list, list]:
    doc_route = "/en/dokumenti/" if locale == "en" else "/dokumenti/"
    lib_route = "/en/biblioteka/" if locale == "en" else "/biblioteka/"
    doc_page = get_page_by_route(db, route_path=doc_route, locale=locale, include_drafts=include_drafts)
    lib_page = get_page_by_route(db, route_path=lib_route, locale=locale, include_drafts=include_drafts)
    doc_groups = document_catalog_from_html(doc_page.body_html, max_items=24) if doc_page else []
    library_entries = library_catalog_from_html(lib_page.body_html, max_items=24) if lib_page else []
    return doc_groups, library_entries


def _render_home(request: Request, db: Session, settings: Settings, *, locale: str):
    include_drafts = preview_enabled(settings)
    page = get_page_by_key(db, page_key="home", locale=locale, include_drafts=include_drafts)
    if page is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="public home is not available")
    context = _common_context(request, db=db, settings=settings, locale=locale, page=page)
    heritage = get_page_by_key(db, page_key="legacy.nasledje", locale=locale, include_drafts=include_drafts)
    context["heritage"] = heritage
    doc_groups, library_entries = _preview_catalogs(db, locale=locale, include_drafts=include_drafts)
    context["home_document_groups"] = doc_groups
    context["home_library_entries"] = library_entries
    return templates.TemplateResponse(request=request, name="index.html", context=context)


def _render_platform(request: Request, db: Session, settings: Settings, *, locale: str, page_key: str):
    include_drafts = preview_enabled(settings)
    page = get_page_by_key(db, page_key=page_key, locale=locale, include_drafts=include_drafts)
    if page is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="platform page is not available")
    context = _common_context(request, db=db, settings=settings, locale=locale, page=page)
    return templates.TemplateResponse(request=request, name="platform.html", context=context)


def _render_route(request: Request, db: Session, settings: Settings, *, locale: str, route_path: str):
    include_drafts = preview_enabled(settings)
    page = get_page_by_route(db, route_path=route_path, locale=locale, include_drafts=include_drafts)
    if page is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="public page not found")
    context = _common_context(request, db=db, settings=settings, locale=locale, page=page)
    if page.page_type == "platform":
        return templates.TemplateResponse(request=request, name="platform.html", context=context)
    if page.page_type == "document_index":
        groups = document_catalog_from_html(page.body_html)
        context["document_groups"] = groups
        context["document_count"] = sum(len(group.items) for group in groups)
        return templates.TemplateResponse(request=request, name="documents.html", context=context)
    if page.page_type == "library_index":
        entries = library_catalog_from_html(page.body_html)
        context["library_entries"] = entries
        context["library_collections"] = sorted({entry.collection for entry in entries})
        return templates.TemplateResponse(request=request, name="library.html", context=context)
    if page.page_type == "program" and page.page_key == "legacy.inkluzivni-razvoj":
        return templates.TemplateResponse(request=request, name="inclusive_development.html", context=context)
    if page.page_key == "legacy.aktivnosti" or route_path.rstrip("/").endswith("/aktivnosti"):
        activities = activity_catalog_from_html(page.body_html)
        context["activities"] = activities
        context["featured_activity"] = activities[0] if activities else None
        context["activity_cards"] = activities[1:7] if len(activities) > 1 else []
        context["activity_results"] = [entry for entry in activities if entry.kind == "Publikacija"][:3]
        return templates.TemplateResponse(request=request, name="activities.html", context=context)
    return templates.TemplateResponse(request=request, name="page.html", context=context)


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def public_home(request: Request, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    return _render_home(request, db, settings, locale="sr-Latn")


@router.get("/en/", response_class=HTMLResponse, include_in_schema=False)
def public_home_en(request: Request, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    return _render_home(request, db, settings, locale="en")


@router.get("/simpa/", response_class=HTMLResponse, include_in_schema=False)
def public_simpa(request: Request, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    return _render_platform(request, db, settings, locale="sr-Latn", page_key="platform.simpa")


@router.get("/ordo/", response_class=HTMLResponse, include_in_schema=False)
def public_ordo(request: Request, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    return _render_platform(request, db, settings, locale="sr-Latn", page_key="platform.ordo")


@router.get("/en/simpa/", response_class=HTMLResponse, include_in_schema=False)
def public_simpa_en(request: Request, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    return _render_platform(request, db, settings, locale="en", page_key="platform.simpa")


@router.get("/en/ordo/", response_class=HTMLResponse, include_in_schema=False)
def public_ordo_en(request: Request, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    return _render_platform(request, db, settings, locale="en", page_key="platform.ordo")


@router.get("/en/{slug}/", response_class=HTMLResponse, include_in_schema=False)
def public_page_en(slug: str, request: Request, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    return _render_route(request, db, settings, locale="en", route_path=f"/en/{slug}/")


@router.get("/{slug}/", response_class=HTMLResponse, include_in_schema=False)
def public_page_sr(slug: str, request: Request, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    if slug in {"api", "static", "media", "app"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return _render_route(request, db, settings, locale="sr-Latn", route_path=f"/{slug}/")


router.include_router(readiness_router)
