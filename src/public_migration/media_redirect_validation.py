from __future__ import annotations

import csv
import hashlib
import json
import mimetypes
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlsplit, urlunsplit

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.public_content.models import (
    PublicLegacySource,
    PublicMediaAsset,
    PublicPage,
    PublicPageTranslation,
    PublicRedirect,
)

BASE_URL = "https://isi.rs/"
ALLOWED_MEDIA_HOSTS = {"isi.rs", "www.isi.rs"}
DEFAULT_MAX_ASSET_BYTES = 200 * 1024 * 1024
READ_ONLY_USER_AGENT = "ISI-Legacy-Media-Migration/1.0 (+https://isi.rs/)"


@dataclass(frozen=True)
class RewriteResult:
    value: str
    kind: str
    unresolved: str = ""


def _json_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalized_host(value: str) -> str:
    host = (urlsplit(value).hostname or "").lower()
    return host


def _safe_extension(source_url: str, content_type: str) -> str:
    suffix = Path(urlsplit(source_url).path).suffix.lower()
    if suffix and len(suffix) <= 10 and re.fullmatch(r"\.[a-z0-9]+", suffix):
        return suffix
    normalized_type = (content_type or "").split(";", 1)[0].strip().lower()
    guessed = mimetypes.guess_extension(normalized_type) or ""
    if guessed == ".jpe":
        guessed = ".jpg"
    return guessed if re.fullmatch(r"\.[a-z0-9]+", guessed or "") else ".bin"


def public_media_url(storage_path: str) -> str:
    clean = storage_path.lstrip("/")
    return f"/media/{clean}"


def _local_media_path(storage_root: Path, storage_path: str) -> Path:
    return storage_root / storage_path


def _existing_verified_asset(asset: PublicMediaAsset, storage_root: Path) -> bool:
    if asset.migration_status != "verified" or not asset.storage_path or not asset.content_sha256:
        return False
    path = _local_media_path(storage_root, asset.storage_path)
    return path.is_file() and _sha256_file(path) == asset.content_sha256


def download_media_assets(
    session: Session,
    *,
    storage_root: str | Path,
    manifest_path: str | Path,
    timeout_seconds: float = 30.0,
    max_asset_bytes: int = DEFAULT_MAX_ASSET_BYTES,
    client: httpx.Client | None = None,
) -> dict[str, object]:
    """Download only committed same-site legacy media using read-only GET requests.

    Binary files are content-addressed by SHA-256. Duplicate source URLs/content share
    one storage blob. Database rows keep source provenance and point to the shared blob.
    """
    storage_root = Path(storage_root)
    manifest_path = Path(manifest_path)
    storage_root.mkdir(parents=True, exist_ok=True)
    temp_root = storage_root / ".tmp"
    temp_root.mkdir(parents=True, exist_ok=True)

    assets = session.scalars(select(PublicMediaAsset).order_by(PublicMediaAsset.source_url)).all()
    records: list[dict[str, object]] = []
    failures: list[dict[str, str]] = []
    seen_hashes: dict[str, str] = {}
    unique_blobs: set[str] = set()
    total_bytes = 0
    skipped_verified = 0

    owns_client = client is None
    if client is None:
        client = httpx.Client(
            follow_redirects=True,
            timeout=timeout_seconds,
            headers={"User-Agent": READ_ONLY_USER_AGENT},
        )

    try:
        for asset in assets:
            source_url = asset.source_url
            if _normalized_host(source_url) not in ALLOWED_MEDIA_HOSTS:
                failures.append({"source_url": source_url, "error": "source host is outside isi.rs"})
                continue

            if _existing_verified_asset(asset, storage_root):
                skipped_verified += 1
                unique_blobs.add(asset.content_sha256)
                records.append(
                    {
                        "source_url": source_url,
                        "status": "verified_existing",
                        "storage_path": asset.storage_path,
                        "public_url": public_media_url(asset.storage_path),
                        "sha256": asset.content_sha256,
                        "mime_type": asset.mime_type,
                        "bytes": _local_media_path(storage_root, asset.storage_path).stat().st_size,
                        "duplicate_of": "",
                    }
                )
                continue

            temp_fd, temp_name = tempfile.mkstemp(prefix="isi-media-", dir=temp_root)
            os.close(temp_fd)
            temp_path = Path(temp_name)
            digest = hashlib.sha256()
            byte_count = 0
            content_type = ""
            final_url = source_url
            try:
                with client.stream("GET", source_url) as response:
                    response.raise_for_status()
                    final_url = str(response.url)
                    if _normalized_host(final_url) not in ALLOWED_MEDIA_HOSTS:
                        raise ValueError(f"redirected outside isi.rs: {final_url}")
                    content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
                    if content_type == "text/html":
                        raise ValueError("asset URL returned text/html")
                    with temp_path.open("wb") as handle:
                        for chunk in response.iter_bytes(1024 * 1024):
                            if not chunk:
                                continue
                            byte_count += len(chunk)
                            if byte_count > max_asset_bytes:
                                raise ValueError(f"asset exceeds max size {max_asset_bytes} bytes")
                            digest.update(chunk)
                            handle.write(chunk)
                if byte_count <= 0:
                    raise ValueError("empty asset response")

                sha256 = digest.hexdigest()
                extension = _safe_extension(final_url, content_type)
                relative_path = Path("legacy") / sha256[:2] / f"{sha256}{extension}"
                destination = storage_root / relative_path
                destination.parent.mkdir(parents=True, exist_ok=True)
                duplicate_of = seen_hashes.get(sha256, "")
                if destination.exists():
                    if _sha256_file(destination) != sha256:
                        raise ValueError(f"existing content-addressed blob hash mismatch: {destination}")
                    temp_path.unlink(missing_ok=True)
                else:
                    temp_path.replace(destination)
                seen_hashes.setdefault(sha256, source_url)
                unique_blobs.add(sha256)
                total_bytes += byte_count

                asset.migration_status = "verified"
                asset.storage_path = relative_path.as_posix()
                asset.content_sha256 = sha256
                asset.mime_type = content_type or mimetypes.guess_type(destination.name)[0] or "application/octet-stream"

                records.append(
                    {
                        "source_url": source_url,
                        "final_url": final_url,
                        "status": "verified",
                        "storage_path": asset.storage_path,
                        "public_url": public_media_url(asset.storage_path),
                        "sha256": sha256,
                        "mime_type": asset.mime_type,
                        "bytes": byte_count,
                        "duplicate_of": duplicate_of,
                    }
                )
            except Exception as exc:  # noqa: BLE001 - migration report must preserve exact failure
                temp_path.unlink(missing_ok=True)
                failures.append({"source_url": source_url, "error": f"{type(exc).__name__}: {exc}"})
    finally:
        if owns_client:
            client.close()
        try:
            temp_root.rmdir()
        except OSError:
            pass

    manifest = {
        "schema_version": 1,
        "storage_root": str(storage_root),
        "assets_total": len(assets),
        "records_total": len(records),
        "verified_count": sum(1 for row in records if str(row["status"]).startswith("verified")),
        "skipped_verified": skipped_verified,
        "failure_count": len(failures),
        "unique_blob_count": len(unique_blobs),
        "duplicate_asset_count": sum(1 for row in records if row.get("duplicate_of")),
        "downloaded_bytes": total_bytes,
        "records": records,
        "failures": failures,
        "source_policy": "read_only_get_same_site",
        "storage_policy": "content_addressed_sha256",
    }
    _json_write(manifest_path, manifest)
    if failures:
        raise RuntimeError(f"Legacy media migration failed for {len(failures)} asset(s); see {manifest_path}")
    return manifest


def _same_site_absolute(value: str) -> str | None:
    parsed = urlsplit(value)
    if parsed.scheme in {"http", "https"} and (parsed.hostname or "").lower() in ALLOWED_MEDIA_HOSTS:
        return value
    if value.startswith("/"):
        return urljoin(BASE_URL, value)
    return None


def _with_query_fragment(path: str, source_value: str) -> str:
    original = urlsplit(source_value)
    target = urlsplit(path)
    return urlunsplit(("", "", target.path, original.query, original.fragment))


def build_migration_maps(session: Session) -> dict[str, dict]:
    assets = session.scalars(select(PublicMediaAsset)).all()
    asset_by_url = {
        asset.source_url: public_media_url(asset.storage_path)
        for asset in assets
        if asset.migration_status == "verified" and asset.storage_path
    }
    asset_by_path = {
        urlsplit(asset.source_url).path: public_media_url(asset.storage_path)
        for asset in assets
        if asset.migration_status == "verified" and asset.storage_path
    }

    translations = session.scalars(select(PublicPageTranslation)).all()
    canonical_routes = {translation.route_path for translation in translations}
    translation_by_page_locale = {(translation.page_id, translation.locale): translation.route_path for translation in translations}

    sources = session.scalars(select(PublicLegacySource)).all()
    route_by_source_url: dict[str, str] = {}
    route_by_legacy_locale: dict[tuple[str, str], str] = {}
    for source in sources:
        if source.mapped_page_id is None:
            continue
        route = translation_by_page_locale.get((source.mapped_page_id, source.locale))
        if route:
            route_by_source_url[source.source_url] = route
            route_by_legacy_locale[(source.legacy_path, source.locale)] = route

    return {
        "asset_by_url": asset_by_url,
        "asset_by_path": asset_by_path,
        "canonical_routes": {route: route for route in canonical_routes},
        "route_by_source_url": route_by_source_url,
        "route_by_legacy_locale": route_by_legacy_locale,
    }


def rewrite_internal_url(value: str, *, locale: str, maps: dict[str, dict]) -> RewriteResult:
    value = (value or "").strip()
    if not value or value.startswith(("#", "mailto:", "tel:", "data:")):
        return RewriteResult(value=value, kind="unchanged")
    if value.lower().startswith("javascript:"):
        return RewriteResult(value="#", kind="unsafe_removed")

    absolute = _same_site_absolute(value)
    if absolute is None:
        return RewriteResult(value=value, kind="external")

    parsed = urlsplit(absolute)
    normalized_source = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query, ""))
    path = parsed.path or "/"

    if normalized_source in maps["asset_by_url"]:
        return RewriteResult(
            value=_with_query_fragment(maps["asset_by_url"][normalized_source], value),
            kind="media",
        )
    if path in maps["asset_by_path"]:
        return RewriteResult(value=_with_query_fragment(maps["asset_by_path"][path], value), kind="media")

    if normalized_source in maps["route_by_source_url"]:
        return RewriteResult(
            value=_with_query_fragment(maps["route_by_source_url"][normalized_source], value),
            kind="page",
        )
    route = maps["route_by_legacy_locale"].get((path, locale))
    if route:
        return RewriteResult(value=_with_query_fragment(route, value), kind="page")
    if path in maps["canonical_routes"]:
        return RewriteResult(value=_with_query_fragment(path, value), kind="canonical")

    if path.startswith("/wp-content/"):
        return RewriteResult(value=value, kind="unresolved", unresolved=f"unmapped media path: {path}")
    return RewriteResult(value=value, kind="unresolved", unresolved=f"unmapped internal path: {path}")


def _rewrite_srcset(value: str, *, locale: str, maps: dict[str, dict]) -> tuple[str, list[RewriteResult]]:
    rendered: list[str] = []
    results: list[RewriteResult] = []
    for raw_candidate in value.split(","):
        candidate = raw_candidate.strip()
        if not candidate:
            continue
        parts = candidate.split()
        url = parts[0]
        descriptor = " ".join(parts[1:])
        result = rewrite_internal_url(url, locale=locale, maps=maps)
        results.append(result)
        rendered.append(result.value + (f" {descriptor}" if descriptor else ""))
    return ", ".join(rendered), results


def normalize_draft_links(session: Session, *, report_path: str | Path) -> dict[str, object]:
    maps = build_migration_maps(session)
    translations = session.scalars(
        select(PublicPageTranslation)
        .join(PublicPage, PublicPage.id == PublicPageTranslation.page_id)
        .where(PublicPage.status == "draft")
        .order_by(PublicPageTranslation.route_path)
    ).all()

    counts = {
        "translations": len(translations),
        "links_seen": 0,
        "media_rewritten": 0,
        "pages_rewritten": 0,
        "canonical_internal": 0,
        "external_links": 0,
        "unsafe_removed": 0,
        "unresolved_internal": 0,
        "translations_changed": 0,
    }
    unresolved: list[dict[str, str]] = []

    for translation in translations:
        soup = BeautifulSoup(translation.body_html or "", "html.parser")
        changed = False
        for tag in soup.find_all(True):
            for attribute in ("href", "src", "poster"):
                if not tag.has_attr(attribute):
                    continue
                original = str(tag.get(attribute) or "")
                counts["links_seen"] += 1
                result = rewrite_internal_url(original, locale=translation.locale, maps=maps)
                if result.kind == "media":
                    counts["media_rewritten"] += 1
                elif result.kind == "page":
                    counts["pages_rewritten"] += 1
                elif result.kind == "canonical":
                    counts["canonical_internal"] += 1
                elif result.kind == "external":
                    counts["external_links"] += 1
                elif result.kind == "unsafe_removed":
                    counts["unsafe_removed"] += 1
                elif result.kind == "unresolved":
                    counts["unresolved_internal"] += 1
                    unresolved.append(
                        {
                            "route_path": translation.route_path,
                            "locale": translation.locale,
                            "attribute": attribute,
                            "value": original,
                            "reason": result.unresolved,
                        }
                    )
                if result.value != original:
                    tag[attribute] = result.value
                    changed = True

            if tag.has_attr("srcset"):
                original = str(tag.get("srcset") or "")
                new_value, results = _rewrite_srcset(original, locale=translation.locale, maps=maps)
                counts["links_seen"] += len(results)
                for result in results:
                    if result.kind == "media":
                        counts["media_rewritten"] += 1
                    elif result.kind == "page":
                        counts["pages_rewritten"] += 1
                    elif result.kind == "canonical":
                        counts["canonical_internal"] += 1
                    elif result.kind == "external":
                        counts["external_links"] += 1
                    elif result.kind == "unsafe_removed":
                        counts["unsafe_removed"] += 1
                    elif result.kind == "unresolved":
                        counts["unresolved_internal"] += 1
                        unresolved.append(
                            {
                                "route_path": translation.route_path,
                                "locale": translation.locale,
                                "attribute": "srcset",
                                "value": original,
                                "reason": result.unresolved,
                            }
                        )
                if new_value != original:
                    tag["srcset"] = new_value
                    changed = True

        if changed:
            translation.body_html = str(soup)
            counts["translations_changed"] += 1

    report = {
        "schema_version": 1,
        **counts,
        "unresolved": unresolved,
        "policy": "all same-site page/media links must resolve before migration acceptance",
        "external_policy": "external links are preserved and do not block migration acceptance",
    }
    _json_write(Path(report_path), report)
    return report


def finalize_redirect_plan(session: Session, *, csv_path: str | Path) -> dict[str, object]:
    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    translations = session.scalars(select(PublicPageTranslation)).all()
    route_by_page_locale = {(row.page_id, row.locale): row.route_path for row in translations}
    sources = session.scalars(select(PublicLegacySource)).all()
    source_by_path_locale = {(row.legacy_path, row.locale): row for row in sources}

    rows: list[dict[str, object]] = []
    unresolved: list[dict[str, str]] = []
    redirects = session.scalars(select(PublicRedirect).order_by(PublicRedirect.legacy_path, PublicRedirect.locale)).all()
    for redirect in redirects:
        source = source_by_path_locale.get((redirect.legacy_path, redirect.locale))
        if source is None or source.mapped_page_id is None:
            unresolved.append({"legacy_path": redirect.legacy_path, "locale": redirect.locale, "reason": "legacy source mapping missing"})
            continue
        target = route_by_page_locale.get((source.mapped_page_id, redirect.locale))
        if not target:
            unresolved.append({"legacy_path": redirect.legacy_path, "locale": redirect.locale, "reason": "target translation missing"})
            continue

        redirect.target_path = target
        redirect.http_status_code = 301
        if redirect.legacy_path == target:
            action = "preserve"
            redirect.status = "disabled"
            redirect.notes = "Legacy path is preserved as the canonical migrated route; redirect not required."
        else:
            action = "redirect"
            redirect.status = "approved"
            redirect.notes = "Canonical legacy alias redirect approved by ISI-03C; activation occurs only in public routing/cutover."
        rows.append(
            {
                "legacy_path": redirect.legacy_path,
                "locale": redirect.locale,
                "action": action,
                "target_path": target,
                "http_status_code": 301 if action == "redirect" else "",
                "db_status": redirect.status,
                "notes": redirect.notes,
            }
        )

    if unresolved:
        raise ValueError(f"Unresolved redirect mapping(s): {unresolved}")

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["legacy_path", "locale", "action", "target_path", "http_status_code", "db_status", "notes"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return {
        "redirect_records": len(rows),
        "preserve_count": sum(1 for row in rows if row["action"] == "preserve"),
        "redirect_count": sum(1 for row in rows if row["action"] == "redirect"),
        "pending_count": 0,
        "policy": "preserve canonical legacy routes; approve only unambiguous aliases; activation deferred to public routing/cutover",
    }


def validate_internal_links(session: Session, *, storage_root: str | Path) -> dict[str, object]:
    storage_root = Path(storage_root)
    maps = build_migration_maps(session)
    translations = session.scalars(select(PublicPageTranslation).order_by(PublicPageTranslation.route_path)).all()
    unresolved: list[dict[str, str]] = []
    internal_checked = 0
    external_seen = 0

    for translation in translations:
        soup = BeautifulSoup(translation.body_html or "", "html.parser")
        values: list[tuple[str, str]] = []
        for tag in soup.find_all(True):
            for attr in ("href", "src", "poster"):
                if tag.has_attr(attr):
                    values.append((attr, str(tag.get(attr) or "")))
            if tag.has_attr("srcset"):
                for candidate in str(tag.get("srcset") or "").split(","):
                    url = candidate.strip().split(" ", 1)[0]
                    if url:
                        values.append(("srcset", url))
        for attr, value in values:
            if not value or value.startswith(("#", "mailto:", "tel:", "data:")):
                continue
            parsed = urlsplit(value)
            if parsed.scheme in {"http", "https"} and (parsed.hostname or "").lower() not in ALLOWED_MEDIA_HOSTS:
                external_seen += 1
                continue
            if parsed.scheme in {"http", "https"}:
                unresolved.append({"route_path": translation.route_path, "attribute": attr, "value": value, "reason": "same-site absolute URL remains after normalization"})
                continue
            if not value.startswith("/"):
                continue
            internal_checked += 1
            path = parsed.path
            if path.startswith("/media/"):
                storage_path = path.removeprefix("/media/")
                file_path = storage_root / storage_path
                if not file_path.is_file():
                    unresolved.append({"route_path": translation.route_path, "attribute": attr, "value": value, "reason": "local media blob missing"})
            elif path not in maps["canonical_routes"]:
                unresolved.append({"route_path": translation.route_path, "attribute": attr, "value": value, "reason": "internal route not present in migrated route set"})

    return {
        "translations": len(translations),
        "internal_links_checked": internal_checked,
        "external_links_seen": external_seen,
        "unresolved_count": len(unresolved),
        "unresolved": unresolved,
    }


def validate_media_storage(session: Session, *, storage_root: str | Path) -> dict[str, object]:
    storage_root = Path(storage_root)
    assets = session.scalars(select(PublicMediaAsset).order_by(PublicMediaAsset.source_url)).all()
    errors: list[dict[str, str]] = []
    hashes: set[str] = set()
    for asset in assets:
        if asset.migration_status != "verified":
            errors.append({"source_url": asset.source_url, "error": f"status={asset.migration_status}"})
            continue
        if not asset.storage_path or not asset.content_sha256:
            errors.append({"source_url": asset.source_url, "error": "storage/hash metadata missing"})
            continue
        path = storage_root / asset.storage_path
        if not path.is_file():
            errors.append({"source_url": asset.source_url, "error": f"storage file missing: {path}"})
            continue
        actual = _sha256_file(path)
        if actual != asset.content_sha256:
            errors.append({"source_url": asset.source_url, "error": f"sha256 mismatch: {actual}"})
            continue
        hashes.add(actual)
    return {
        "assets_total": len(assets),
        "verified_assets": len(assets) - len(errors),
        "unique_blobs": len(hashes),
        "error_count": len(errors),
        "errors": errors,
    }


def build_acceptance_report(
    session: Session,
    *,
    storage_root: str | Path,
    media_manifest_path: str | Path,
    link_report_path: str | Path,
    final_redirect_csv: str | Path,
    output_path: str | Path,
) -> dict[str, object]:
    media = validate_media_storage(session, storage_root=storage_root)
    links = validate_internal_links(session, storage_root=storage_root)
    pages_non_draft = session.scalars(select(PublicPage).where(PublicPage.status != "draft")).all()
    pending_redirects = session.scalars(select(PublicRedirect).where(PublicRedirect.status == "pending")).all()
    approved_redirects = session.scalars(select(PublicRedirect).where(PublicRedirect.status == "approved")).all()
    preserved_routes = session.scalars(select(PublicRedirect).where(PublicRedirect.status == "disabled")).all()

    required_artifacts = [Path(media_manifest_path), Path(link_report_path), Path(final_redirect_csv)]
    missing_artifacts = [str(path) for path in required_artifacts if not path.is_file()]
    passed = not media["error_count"] and not links["unresolved_count"] and not pages_non_draft and not pending_redirects and not missing_artifacts
    report = {
        "schema_version": 1,
        "acceptance_passed": passed,
        "media": media,
        "links": links,
        "publication": {
            "non_draft_pages": len(pages_non_draft),
            "policy": "legacy import remains draft-only",
        },
        "redirects": {
            "approved_alias_redirects": len(approved_redirects),
            "preserved_routes": len(preserved_routes),
            "pending_redirects": len(pending_redirects),
            "activation_policy": "approved mappings are data only; no redirect middleware/cutover activation in ISI-03C",
        },
        "missing_artifacts": missing_artifacts,
        "external_link_policy": "external links are preserved and reported but are not migration-blocking dependencies",
    }
    _json_write(Path(output_path), report)
    return report
