from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import bleach
import httpx
from bs4 import BeautifulSoup

from src.public_migration.legacy_inventory import _PageParser

ALLOWED_TAGS = set(bleach.sanitizer.ALLOWED_TAGS) | {
    "p", "br", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li",
    "blockquote", "figure", "figcaption", "img", "hr", "div", "span",
}
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title"],
    "img": ["src", "alt", "title", "width", "height"],
    "blockquote": ["cite"],
}
CONTENT_SELECTORS = (
    ".entry-content",
    ".wp-block-post-content",
    ".elementor-widget-theme-post-content",
    "article .post-content",
    "main article",
    "main",
    "article",
    "#content",
    "body",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _same_origin(url: str, base_url: str) -> bool:
    a = urlparse(url)
    b = urlparse(base_url)
    ah = a.netloc.lower().removeprefix("www.")
    bh = b.netloc.lower().removeprefix("www.")
    return a.scheme in {"http", "https"} and ah == bh


def _normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _inventory_style_hash(html: str) -> str:
    parser = _PageParser()
    parser.feed(html)
    body = parser.body_text
    return hashlib.sha256(body.encode("utf-8")).hexdigest() if body else ""


def extract_public_content(html: str, source_url: str) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    page_title = ""
    title_node = soup.find("title")
    if title_node is not None:
        page_title = _normalize_space(title_node.get_text(" ", strip=True))
    for node in soup.select("script, style, noscript, nav, footer, form"):
        node.decompose()

    candidate = None
    method = ""
    for selector in CONTENT_SELECTORS:
        found = soup.select_one(selector)
        if found is not None and _normalize_space(found.get_text(" ", strip=True)):
            candidate = found
            method = selector
            break
    if candidate is None:
        raise ValueError("No non-empty content container found")

    for node in candidate.find_all(["header", "nav", "footer", "script", "style", "noscript", "form"]):
        node.decompose()
    first_h1 = candidate.find("h1")
    heading = _normalize_space(first_h1.get_text(" ", strip=True)) if first_h1 is not None else page_title
    for tag in candidate.find_all(True):
        if tag.name == "a" and tag.get("href"):
            tag["href"] = urljoin(source_url, tag["href"])
        if tag.name == "img" and tag.get("src"):
            tag["src"] = urljoin(source_url, tag["src"])

    raw_fragment = "".join(str(child) for child in candidate.contents)
    clean_html = bleach.clean(
        raw_fragment,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols={"http", "https", "mailto", "tel"},
        strip=True,
        strip_comments=True,
    )
    clean_soup = BeautifulSoup(clean_html, "html.parser")
    body_text = _normalize_space(clean_soup.get_text(" ", strip=True))
    return {
        "body_html": clean_html.strip(),
        "body_text": body_text,
        "content_title": heading,
        "extraction_method": method,
    }


@dataclass(frozen=True)
class LegacySnapshotRecord:
    source_url: str
    legacy_path: str
    language: str
    http_status: int
    fetched_at: str
    source_html_sha256: str
    inventory_content_sha256: str
    current_inventory_style_sha256: str
    inventory_drift: bool
    content_sha256: str
    content_chars: int
    content_title: str
    extraction_method: str
    snapshot_file: str
    error: str = ""


def capture_snapshots(
    inventory_path: str | Path,
    output_dir: str | Path,
    *,
    timeout_seconds: float = 20.0,
) -> dict[str, object]:
    inventory_path = Path(inventory_path)
    output_dir = Path(output_dir)
    payload = json.loads(inventory_path.read_text(encoding="utf-8"))
    base_url = payload["base_url"]
    pages = [
        row for row in payload["pages"]
        if row.get("content_type") == "page" and 200 <= int(row.get("http_status", 0)) < 400
    ]
    output_dir.mkdir(parents=True, exist_ok=True)
    for old in output_dir.glob("*.json"):
        old.unlink()

    records: list[LegacySnapshotRecord] = []
    headers = {"User-Agent": "ISI-Legacy-Migration-Snapshot/1.0 (+https://isi.rs/)"}
    with httpx.Client(follow_redirects=True, timeout=timeout_seconds, headers=headers) as client:
        for page in pages:
            url = page["source_url"]
            if not _same_origin(url, base_url):
                raise ValueError(f"Refusing cross-origin snapshot URL: {url}")
            try:
                response = client.get(url)
                response.raise_for_status()
                ctype = response.headers.get("content-type", "").lower()
                if "text/html" not in ctype:
                    raise ValueError(f"Expected text/html, got {ctype!r}")
                source_hash = hashlib.sha256(response.text.encode("utf-8")).hexdigest()
                inventory_style_hash = _inventory_style_hash(response.text)
                expected_hash = page.get("content_sha256", "")
                extracted = extract_public_content(response.text, str(response.url))
                body_text = extracted["body_text"]
                if not body_text:
                    raise ValueError("Extracted public content is empty")
                snapshot_name = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24] + ".json"
                snapshot_payload = {
                    "schema_version": 1,
                    "source_url": url,
                    "legacy_path": page["legacy_path"],
                    "language": page["language"],
                    "fetched_at": _now_iso(),
                    "content_title": extracted["content_title"],
                    "body_html": extracted["body_html"],
                    "body_text": body_text,
                    "content_sha256": hashlib.sha256(body_text.encode("utf-8")).hexdigest(),
                    "source_html_sha256": source_hash,
                    "inventory_content_sha256": expected_hash,
                    "current_inventory_style_sha256": inventory_style_hash,
                    "extraction_method": extracted["extraction_method"],
                }
                (output_dir / snapshot_name).write_text(
                    json.dumps(snapshot_payload, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                records.append(
                    LegacySnapshotRecord(
                        source_url=url,
                        legacy_path=page["legacy_path"],
                        language=page["language"],
                        http_status=response.status_code,
                        fetched_at=snapshot_payload["fetched_at"],
                        source_html_sha256=source_hash,
                        inventory_content_sha256=expected_hash,
                        current_inventory_style_sha256=inventory_style_hash,
                        inventory_drift=bool(expected_hash and inventory_style_hash != expected_hash),
                        content_sha256=snapshot_payload["content_sha256"],
                        content_chars=len(body_text),
                        content_title=extracted["content_title"],
                        extraction_method=extracted["extraction_method"],
                        snapshot_file=str((output_dir / snapshot_name).as_posix()),
                    )
                )
            except Exception as exc:  # noqa: BLE001 - capture report must preserve failures
                records.append(
                    LegacySnapshotRecord(
                        source_url=url,
                        legacy_path=page["legacy_path"],
                        language=page["language"],
                        http_status=0,
                        fetched_at=_now_iso(),
                        source_html_sha256="",
                        inventory_content_sha256=page.get("content_sha256", ""),
                        current_inventory_style_sha256="",
                        inventory_drift=False,
                        content_sha256="",
                        content_chars=0,
                        content_title="",
                        extraction_method="",
                        snapshot_file="",
                        error=f"{type(exc).__name__}: {exc}",
                    )
                )

    manifest = {
        "schema_version": 1,
        "base_url": base_url,
        "generated_at": _now_iso(),
        "expected_pages": len(pages),
        "snapshot_records": [asdict(record) for record in records],
        "success_count": sum(1 for record in records if not record.error),
        "failure_count": sum(1 for record in records if record.error),
        "drift_count": sum(1 for record in records if record.inventory_drift),
    }
    manifest_path = output_dir.parent / "snapshot_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest
