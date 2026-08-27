from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.public_content.models import (
    PublicLegacySource,
    PublicMediaAsset,
    PublicPage,
    PublicPageTranslation,
    PublicRedirect,
)


def _parse_dt(value: str | None):
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _route_without_locale(path: str) -> str:
    route = (path or "/").split("?", 1)[0]
    if route == "/en" or route == "/en/":
        return "/"
    if route.startswith("/en/"):
        return "/" + route[len("/en/"):]
    return route


def page_key_for(legacy_path: str, locale: str) -> str:
    normalized = _route_without_locale(legacy_path)
    if legacy_path in {"/", "/en/homepage-english/", "/en/homepage-english", "/en/", "/en"}:
        return "home"
    normalized = normalized.strip("/")
    if normalized == "homepage-english":
        return "home"
    parts = [re.sub(r"[^a-z0-9-]+", "-", part.lower()).strip("-") for part in normalized.split("/")]
    parts = [part for part in parts if part]
    return "legacy." + ".".join(parts or ["home"])


def page_type_for(legacy_path: str) -> str:
    if legacy_path in {"/", "/en/homepage-english/", "/en/homepage-english", "/en/", "/en"}:
        return "home"
    route = _route_without_locale(legacy_path).rstrip("/") or "/"
    mapping = {
        "/": "home",
        "/tim": "team_index",
        "/aktivnosti": "activity_index",
        "/dokumenti": "document_index",
        "/biblioteka": "library_index",
        "/inkluzivni-razvoj": "program",
        "/nasledje": "heritage",
    }
    return mapping.get(route, "standard")


def navigation_meta(legacy_path: str) -> tuple[bool, int]:
    route = _route_without_locale(legacy_path).rstrip("/") or "/"
    order = {
        "/": 0,
        "/tim": 10,
        "/aktivnosti": 20,
        "/dokumenti": 30,
        "/biblioteka": 40,
        "/inkluzivni-razvoj": 50,
        "/nasledje": 60,
    }
    return (route in order and route != "/", order.get(route, 1000))


def _snapshot_map(manifest_path: Path) -> dict[str, dict]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("failure_count") or manifest.get("drift_count"):
        raise ValueError("Snapshot manifest contains failures or source drift")
    return {row["source_url"]: row for row in manifest["snapshot_records"]}


def _load_snapshot(manifest_row: dict, root: Path) -> dict:
    snapshot_file = Path(manifest_row["snapshot_file"])
    if not snapshot_file.is_absolute() and not snapshot_file.exists():
        snapshot_file = root / snapshot_file.name
    return json.loads(snapshot_file.read_text(encoding="utf-8"))


def _canonical_path(row: dict) -> str:
    canonical_url = (row.get("canonical_url") or "").strip()
    if canonical_url:
        path = urlsplit(canonical_url).path
        if path:
            return path
    return row.get("legacy_path") or "/"


def _select_primary_page_row(rows: list[dict]) -> dict:
    """Choose one renderable translation row from a set of legacy aliases.

    Exact agreement with canonical_url wins. Otherwise selection is deterministic.
    All rows remain preserved as PublicLegacySource records and redirects.
    """
    exact = [row for row in rows if row.get("legacy_path") == _canonical_path(row)]
    candidates = exact or rows
    return sorted(
        candidates,
        key=lambda row: (
            len(row.get("legacy_path") or ""),
            row.get("legacy_path") or "",
            row.get("source_url") or "",
        ),
    )[0]


def _logical_page_groups(successful_pages: list[dict]) -> dict[tuple[str, str], list[dict]]:
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in successful_pages:
        groups[(page_key_for(row["legacy_path"], row["language"]), row["language"])].append(row)
    return dict(groups)


def import_legacy_content(
    session: Session,
    *,
    inventory_path: str | Path,
    snapshot_manifest_path: str | Path,
    redirect_map_path: str | Path,
    report_path: str | Path,
) -> dict[str, object]:
    inventory_path = Path(inventory_path)
    snapshot_manifest_path = Path(snapshot_manifest_path)
    redirect_map_path = Path(redirect_map_path)
    report_path = Path(report_path)
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    snapshot_rows = _snapshot_map(snapshot_manifest_path)
    root = snapshot_manifest_path.parent

    successful_pages = [
        row for row in inventory["pages"]
        if row.get("content_type") == "page" and 200 <= int(row.get("http_status", 0)) < 400
    ]
    if set(snapshot_rows) != {row["source_url"] for row in successful_pages}:
        raise ValueError("Snapshot/source set does not match committed inventory")

    groups = _logical_page_groups(successful_pages)
    logical_page_keys = {page_key for page_key, _locale in groups}

    counters = {
        "pages_created": 0,
        "pages_updated": 0,
        "translations_created": 0,
        "translations_updated": 0,
        "sources_created": 0,
        "sources_updated": 0,
        "assets_created": 0,
        "assets_updated": 0,
        "redirects_created": 0,
        "redirects_updated": 0,
    }

    for (key, locale), rows in sorted(groups.items(), key=lambda item: item[0]):
        snapshots_by_url = {
            row["source_url"]: _load_snapshot(snapshot_rows[row["source_url"]], root)
            for row in rows
        }
        content_hashes = {snapshot["content_sha256"] for snapshot in snapshots_by_url.values()}
        if len(content_hashes) != 1:
            aliases = [row["legacy_path"] for row in rows]
            raise ValueError(
                f"Conflicting legacy aliases map to the same page/locale but contain different content: "
                f"page_key={key}, locale={locale}, aliases={aliases}"
            )

        primary_row = _select_primary_page_row(rows)
        primary_snapshot = snapshots_by_url[primary_row["source_url"]]
        is_nav, nav_order = navigation_meta(primary_row["legacy_path"])

        page = session.scalar(select(PublicPage).where(PublicPage.page_key == key))
        if page is None:
            page = PublicPage(
                page_key=key,
                page_type=page_type_for(primary_row["legacy_path"]),
                status="draft",
                navigation_order=nav_order,
                is_navigation=is_nav,
            )
            session.add(page)
            session.flush()
            counters["pages_created"] += 1
        else:
            page.page_type = page_type_for(primary_row["legacy_path"])
            page.status = "draft"
            page.navigation_order = min(page.navigation_order, nav_order)
            page.is_navigation = page.is_navigation or is_nav
            counters["pages_updated"] += 1

        translation = session.scalar(
            select(PublicPageTranslation).where(
                PublicPageTranslation.page_id == page.id,
                PublicPageTranslation.locale == locale,
            )
        )
        route_path = primary_row["legacy_path"]
        route_conflict = session.scalar(
            select(PublicPageTranslation).where(PublicPageTranslation.route_path == route_path)
        )
        if route_conflict is not None and (translation is None or route_conflict.id != translation.id):
            raise ValueError(f"Route path already belongs to another translation: {route_path}")

        values = {
            "route_path": route_path,
            "title": primary_snapshot.get("content_title") or primary_row.get("title", ""),
            "summary": primary_row.get("meta_description", ""),
            "body_html": primary_snapshot["body_html"],
            "body_text": primary_snapshot["body_text"],
            "seo_title": primary_row.get("title", ""),
            "meta_description": primary_row.get("meta_description", ""),
            "source_url": primary_row["source_url"],
            "source_content_sha256": primary_snapshot["content_sha256"],
            "source_fetched_at": _parse_dt(primary_snapshot.get("fetched_at")),
        }
        if translation is None:
            translation = PublicPageTranslation(page_id=page.id, locale=locale, **values)
            session.add(translation)
            counters["translations_created"] += 1
        else:
            for name, value in values.items():
                setattr(translation, name, value)
            counters["translations_updated"] += 1
        session.flush()

        for page_row in rows:
            source_url = page_row["source_url"]
            snapshot = snapshots_by_url[source_url]
            manifest_row = snapshot_rows[source_url]
            source = session.scalar(select(PublicLegacySource).where(PublicLegacySource.source_url == source_url))
            source_values = {
                "legacy_path": page_row["legacy_path"],
                "locale": page_row["language"],
                "title": page_row.get("title", ""),
                "canonical_url": page_row.get("canonical_url", ""),
                "http_status": int(page_row["http_status"]),
                "inventory_content_sha256": page_row.get("content_sha256", ""),
                "snapshot_content_sha256": snapshot["content_sha256"],
                "source_html_sha256": snapshot["source_html_sha256"],
                "snapshot_file": manifest_row["snapshot_file"],
                "extraction_method": snapshot["extraction_method"],
                "mapping_status": "mapped_page",
                "mapped_page_id": page.id,
                "source_fetched_at": _parse_dt(snapshot.get("fetched_at")),
            }
            if source is None:
                session.add(PublicLegacySource(source_url=source_url, **source_values))
                counters["sources_created"] += 1
            else:
                for name, value in source_values.items():
                    setattr(source, name, value)
                counters["sources_updated"] += 1

    for asset_row in inventory.get("assets", []):
        asset = session.scalar(select(PublicMediaAsset).where(PublicMediaAsset.source_url == asset_row["source_url"]))
        values = {
            "legacy_path": asset_row.get("legacy_path", ""),
            "asset_type": asset_row.get("asset_type", "asset"),
            "extension": asset_row.get("extension", ""),
            "locale": asset_row.get("language", "sr-Latn"),
            "discovered_from": asset_row.get("discovered_from", ""),
            "migration_status": "pending",
        }
        if asset is None:
            session.add(PublicMediaAsset(source_url=asset_row["source_url"], **values))
            counters["assets_created"] += 1
        else:
            for name, value in values.items():
                setattr(asset, name, value)
            counters["assets_updated"] += 1

    with redirect_map_path.open(newline="", encoding="utf-8") as handle:
        redirect_rows = list(csv.DictReader(handle))
    for row in redirect_rows:
        redirect = session.scalar(
            select(PublicRedirect).where(
                PublicRedirect.legacy_path == row["legacy_path"],
                PublicRedirect.locale == row["locale"],
            )
        )
        values = {
            "target_path": row["candidate_new_path"],
            "status": "pending",
            "http_status_code": 301,
            "notes": row.get("notes", ""),
        }
        if redirect is None:
            session.add(PublicRedirect(legacy_path=row["legacy_path"], locale=row["locale"], **values))
            counters["redirects_created"] += 1
        else:
            for name, value in values.items():
                setattr(redirect, name, value)
            counters["redirects_updated"] += 1

    session.flush()
    totals = {
        "public_pages": session.scalar(select(func.count()).select_from(PublicPage)),
        "public_page_translations": session.scalar(select(func.count()).select_from(PublicPageTranslation)),
        "public_legacy_sources": session.scalar(select(func.count()).select_from(PublicLegacySource)),
        "public_media_assets": session.scalar(select(func.count()).select_from(PublicMediaAsset)),
        "public_redirects": session.scalar(select(func.count()).select_from(PublicRedirect)),
    }
    report = {
        "schema_version": 1,
        "inventory_base_url": inventory["base_url"],
        "successful_inventory_pages": len(successful_pages),
        "logical_pages": len(logical_page_keys),
        "logical_page_translations": len(groups),
        "legacy_alias_pages": len(successful_pages) - len(groups),
        "inventory_assets": len(inventory.get("assets", [])),
        "redirect_candidates": len(redirect_rows),
        "changes": counters,
        "totals": totals,
        "publication_policy": "draft_only",
        "redirect_policy": "pending_only",
        "alias_policy": "all legacy source URLs preserved; one translation per logical page and locale",
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report
