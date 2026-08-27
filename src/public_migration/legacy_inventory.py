from __future__ import annotations

import csv
import hashlib
import json
import re
import time
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import urldefrag, urljoin, urlparse, urlunparse

import httpx

PAGE_LIKE_EXTENSIONS = {"", ".html", ".htm", ".php"}
DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".csv", ".zip"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico"}
MEDIA_EXTENSIONS = {".mp3", ".mp4", ".wav", ".m4a", ".mov", ".avi", ".webm"}
IGNORED_PATH_PREFIXES = (
    "/wp-admin",
    "/wp-login.php",
    "/wp-json/",
    "/xmlrpc.php",
)
DEFAULT_SEEDS = (
    "/",
    "/tim/",
    "/aktivnosti/",
    "/dokumenti/",
    "/biblioteka",
    "/inkluzivni-razvoj/",
    "/nasledje/",
    "/en/homepage-english/",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _extension(path: str) -> str:
    suffix = Path(path).suffix.lower()
    return suffix if len(suffix) <= 8 else ""


def _classify_asset(path: str) -> str | None:
    ext = _extension(path)
    if ext in DOCUMENT_EXTENSIONS:
        return "document"
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in MEDIA_EXTENSIONS:
        return "media"
    return None


def _is_page_candidate(path: str) -> bool:
    if any(path.startswith(prefix) for prefix in IGNORED_PATH_PREFIXES):
        return False
    return _extension(path) in PAGE_LIKE_EXTENSIONS


def _canonicalize_url(raw_url: str, base_url: str) -> str | None:
    if not raw_url:
        return None
    absolute = urljoin(base_url, raw_url.strip())
    absolute, _ = urldefrag(absolute)
    parsed = urlparse(absolute)
    if parsed.scheme not in {"http", "https"}:
        return None
    host = parsed.netloc.lower()
    base_host = urlparse(base_url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    if base_host.startswith("www."):
        base_host = base_host[4:]
    if host != base_host:
        return None
    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), path, "", parsed.query, ""))


def _path_key(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path or "/"
    if parsed.query:
        return f"{path}?{parsed.query}"
    return path


def _language_for(path: str, html_lang: str | None) -> str:
    if path == "/en" or path.startswith("/en/"):
        return "en"
    if html_lang:
        lower = html_lang.lower()
        if lower.startswith("en"):
            return "en"
        if lower.startswith("sr"):
            return "sr-Latn"
    return "sr-Latn"


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.body_parts: list[str] = []
        self.links: list[str] = []
        self.assets: list[str] = []
        self.canonical: str | None = None
        self.description: str = ""
        self.html_lang: str | None = None
        self._in_title = False
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key.lower(): (value or "") for key, value in attrs}
        tag = tag.lower()
        if tag == "html" and attr.get("lang"):
            self.html_lang = attr["lang"]
        if tag == "title":
            self._in_title = True
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
        if tag == "a" and attr.get("href"):
            self.links.append(attr["href"])
        if tag in {"img", "source", "video", "audio"}:
            for key in ("src", "poster"):
                if attr.get(key):
                    self.assets.append(attr[key])
            if attr.get("srcset"):
                for candidate in attr["srcset"].split(","):
                    value = candidate.strip().split(" ", 1)[0]
                    if value:
                        self.assets.append(value)
        if tag == "link" and attr.get("rel", "").lower() == "canonical" and attr.get("href"):
            self.canonical = attr["href"]
        if tag == "meta" and attr.get("name", "").lower() == "description":
            self.description = attr.get("content", "")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self._in_title = False
        if tag in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)
        if self._skip_depth == 0:
            value = _normalize_space(data)
            if value:
                self.body_parts.append(value)

    @property
    def title(self) -> str:
        return _normalize_space(" ".join(self.title_parts))

    @property
    def body_text(self) -> str:
        return _normalize_space(" ".join(self.body_parts))


@dataclass(frozen=True)
class LegacyPageRecord:
    source_url: str
    legacy_path: str
    title: str
    language: str
    http_status: int
    final_url: str
    canonical_url: str
    meta_description: str
    content_type: str
    content_chars: int
    content_sha256: str
    discovered_from: str
    fetched_at: str
    error: str = ""


@dataclass(frozen=True)
class LegacyAssetRecord:
    source_url: str
    legacy_path: str
    asset_type: str
    extension: str
    language: str
    discovered_from: str


@dataclass(frozen=True)
class InventoryBundle:
    base_url: str
    generated_at: str
    pages: list[LegacyPageRecord]
    assets: list[LegacyAssetRecord]
    failures: list[dict[str, str]]


def crawl_site(
    base_url: str,
    *,
    max_pages: int = 300,
    seeds: Iterable[str] = DEFAULT_SEEDS,
    delay_seconds: float = 0.05,
    timeout_seconds: float = 20.0,
) -> InventoryBundle:
    base_url = base_url.rstrip("/") + "/"
    queue: deque[tuple[str, str]] = deque()
    seen: set[str] = set()
    pages: list[LegacyPageRecord] = []
    assets_by_url: dict[str, LegacyAssetRecord] = {}
    failures: list[dict[str, str]] = []

    for seed in seeds:
        normalized = _canonicalize_url(seed, base_url)
        if normalized:
            queue.append((normalized, "seed"))

    headers = {"User-Agent": "ISI-Legacy-Migration-Inventory/1.0 (+https://isi.rs/)"}
    with httpx.Client(follow_redirects=True, timeout=timeout_seconds, headers=headers) as client:
        while queue and len(pages) < max_pages:
            url, discovered_from = queue.popleft()
            if url in seen:
                continue
            seen.add(url)
            path = _path_key(url)
            if not _is_page_candidate(urlparse(url).path):
                continue
            try:
                response = client.get(url)
            except Exception as exc:  # noqa: BLE001 - inventory must record network failures
                failures.append({"source_url": url, "error": f"{type(exc).__name__}: {exc}"})
                pages.append(
                    LegacyPageRecord(
                        source_url=url,
                        legacy_path=path,
                        title="",
                        language=_language_for(path, None),
                        http_status=0,
                        final_url=url,
                        canonical_url="",
                        meta_description="",
                        content_type="error",
                        content_chars=0,
                        content_sha256="",
                        discovered_from=discovered_from,
                        fetched_at=_now_iso(),
                        error=f"{type(exc).__name__}: {exc}",
                    )
                )
                continue

            content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
            final_url = _canonicalize_url(str(response.url), base_url) or str(response.url)
            if content_type != "text/html":
                pages.append(
                    LegacyPageRecord(
                        source_url=url,
                        legacy_path=path,
                        title="",
                        language=_language_for(path, None),
                        http_status=response.status_code,
                        final_url=final_url,
                        canonical_url="",
                        meta_description="",
                        content_type=content_type or "unknown",
                        content_chars=0,
                        content_sha256="",
                        discovered_from=discovered_from,
                        fetched_at=_now_iso(),
                    )
                )
                continue

            parser = _PageParser()
            parser.feed(response.text)
            body = parser.body_text
            page_language = _language_for(path, parser.html_lang)
            canonical = _canonicalize_url(parser.canonical or "", base_url) or ""
            pages.append(
                LegacyPageRecord(
                    source_url=url,
                    legacy_path=path,
                    title=parser.title,
                    language=page_language,
                    http_status=response.status_code,
                    final_url=final_url,
                    canonical_url=canonical,
                    meta_description=_normalize_space(parser.description),
                    content_type="page",
                    content_chars=len(body),
                    content_sha256=hashlib.sha256(body.encode("utf-8")).hexdigest() if body else "",
                    discovered_from=discovered_from,
                    fetched_at=_now_iso(),
                )
            )

            if response.status_code < 400:
                for raw_link in parser.links:
                    normalized = _canonicalize_url(raw_link, base_url)
                    if not normalized:
                        continue
                    target_path = urlparse(normalized).path
                    asset_type = _classify_asset(target_path)
                    if asset_type:
                        assets_by_url.setdefault(
                            normalized,
                            LegacyAssetRecord(
                                source_url=normalized,
                                legacy_path=_path_key(normalized),
                                asset_type=asset_type,
                                extension=_extension(target_path),
                                language=page_language,
                                discovered_from=url,
                            ),
                        )
                    elif _is_page_candidate(target_path) and normalized not in seen:
                        queue.append((normalized, url))
                for raw_asset in parser.assets:
                    normalized = _canonicalize_url(raw_asset, base_url)
                    if not normalized:
                        continue
                    target_path = urlparse(normalized).path
                    asset_type = _classify_asset(target_path) or "asset"
                    assets_by_url.setdefault(
                        normalized,
                        LegacyAssetRecord(
                            source_url=normalized,
                            legacy_path=_path_key(normalized),
                            asset_type=asset_type,
                            extension=_extension(target_path),
                            language=page_language,
                            discovered_from=url,
                        ),
                    )
            if delay_seconds:
                time.sleep(delay_seconds)

    pages.sort(key=lambda item: (item.legacy_path.lower(), item.source_url))
    assets = sorted(assets_by_url.values(), key=lambda item: (item.legacy_path.lower(), item.source_url))
    return InventoryBundle(base_url=base_url, generated_at=_now_iso(), pages=pages, assets=assets, failures=failures)


def _write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_inventory_artifacts(bundle: InventoryBundle, output_dir: str | Path) -> dict[str, object]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    page_rows = [asdict(item) for item in bundle.pages]
    asset_rows = [asdict(item) for item in bundle.assets]
    payload = {
        "schema_version": 1,
        "base_url": bundle.base_url,
        "generated_at": bundle.generated_at,
        "pages": page_rows,
        "assets": asset_rows,
        "failures": bundle.failures,
    }
    (output / "inventory.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    _write_csv(output / "pages.csv", page_rows, list(LegacyPageRecord.__dataclass_fields__))
    _write_csv(output / "assets.csv", asset_rows, list(LegacyAssetRecord.__dataclass_fields__))

    redirect_rows: list[dict[str, str]] = []
    seen_paths: set[str] = set()
    for page in bundle.pages:
        if page.content_type != "page" or page.legacy_path in seen_paths:
            continue
        seen_paths.add(page.legacy_path)
        redirect_rows.append(
            {
                "legacy_path": page.legacy_path,
                "candidate_new_path": page.legacy_path,
                "locale": page.language,
                "review_status": "pending",
                "notes": "Preserve or replace during ISI-03B content mapping.",
            }
        )
    _write_csv(
        output / "redirect_map.csv",
        redirect_rows,
        ["legacy_path", "candidate_new_path", "locale", "review_status", "notes"],
    )

    success_pages = [item for item in bundle.pages if item.content_type == "page" and 200 <= item.http_status < 400]
    languages = sorted({item.language for item in success_pages})
    summary = {
        "schema_version": 1,
        "base_url": bundle.base_url,
        "generated_at": bundle.generated_at,
        "page_records": len(bundle.pages),
        "successful_html_pages": len(success_pages),
        "asset_records": len(bundle.assets),
        "failure_records": len(bundle.failures),
        "languages": languages,
        "redirect_candidates": len(redirect_rows),
    }
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary
