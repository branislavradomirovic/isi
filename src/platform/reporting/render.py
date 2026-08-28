from __future__ import annotations

import html
import json
import re
from typing import Any


MIME_TYPES = {
    "json": "application/json; charset=utf-8",
    "markdown": "text/markdown; charset=utf-8",
    "html": "text/html; charset=utf-8",
}
EXTENSIONS = {"json": "json", "markdown": "md", "html": "html"}


def safe_slug(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-")
    return value[:120] or "report"


def _value(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.3f}".rstrip("0").rstrip(".")
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def render_json(*, metadata: dict, content: dict, source_manifest: list) -> str:
    return json.dumps(
        {"metadata": metadata, "content": content, "source_manifest": source_manifest},
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
        default=str,
    ) + "\n"


def render_markdown(*, metadata: dict, content: dict, source_manifest: list) -> str:
    lines = [
        f"# {metadata['title']}",
        "",
        f"**Platforma:** {metadata['product_code']}",
        f"**Tip izveštaja:** {metadata['report_type']}",
        f"**Verzija:** {metadata['version_no']}",
        f"**Status:** {metadata['status']}",
        f"**SHA-256 sadržaja:** `{metadata['content_sha256']}`",
        "",
        "> Ovaj artefakt je generisan iz verzionisanog ISI reporting snapshot-a. AI sadržaj, ako postoji, može biti uključen samo nakon evidentiranog human review-a.",
        "",
    ]
    for section in content.get("sections", []):
        lines += [f"## {section.get('title', section.get('key', 'Sekcija'))}", ""]
        if section.get("text"):
            lines += [str(section["text"]), ""]
        metrics = section.get("metrics") or {}
        for key, value in metrics.items():
            lines.append(f"- **{key}:** {_value(value)}")
        if metrics:
            lines.append("")
        rows = section.get("rows") or []
        if rows:
            columns = list(rows[0].keys())
            lines.append("| " + " | ".join(columns) + " |")
            lines.append("| " + " | ".join("---" for _ in columns) + " |")
            for row in rows:
                lines.append("| " + " | ".join(_value(row.get(col)).replace("|", "\\|") for col in columns) + " |")
            lines.append("")
        bullets = section.get("bullets") or []
        for item in bullets:
            lines.append(f"- {_value(item)}")
        if bullets:
            lines.append("")
    lines += ["## Provenance manifest", ""]
    for item in source_manifest:
        lines.append(
            f"- `{item.get('kind')}` · `{item.get('id')}` · product `{item.get('product_code')}` · SHA-256 `{item.get('checksum')}`"
        )
    return "\n".join(lines).rstrip() + "\n"


def render_html(*, metadata: dict, content: dict, source_manifest: list) -> str:
    def esc(value: Any) -> str:
        return html.escape(_value(value))

    chunks = [
        "<!doctype html><html lang='sr'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        f"<title>{esc(metadata['title'])}</title>",
        "<style>body{font-family:system-ui,-apple-system,sans-serif;max-width:980px;margin:48px auto;padding:0 28px;color:#1d2623;line-height:1.55}h1,h2{line-height:1.15}small,.meta{color:#5a6661}.notice{padding:14px 16px;background:#f3f5f2;border-left:4px solid #355f55}table{border-collapse:collapse;width:100%;margin:16px 0}th,td{border:1px solid #d9dfdc;padding:8px;text-align:left;vertical-align:top}code{font-size:.9em}</style>",
        "</head><body>",
        f"<h1>{esc(metadata['title'])}</h1>",
        f"<p class='meta'>Platforma: <strong>{esc(metadata['product_code'])}</strong> · Tip: {esc(metadata['report_type'])} · Verzija: {esc(metadata['version_no'])} · Status: {esc(metadata['status'])}</p>",
        "<p class='notice'>Verzionisani ISI reporting artefakt. AI sadržaj, ako postoji, uključen je samo kada je prethodno evidentiran human review.</p>",
    ]
    for section in content.get("sections", []):
        chunks.append(f"<h2>{esc(section.get('title', section.get('key', 'Sekcija')))}</h2>")
        if section.get("text"):
            chunks.append(f"<p>{esc(section['text'])}</p>")
        metrics = section.get("metrics") or {}
        if metrics:
            chunks.append("<ul>")
            for key, value in metrics.items():
                chunks.append(f"<li><strong>{esc(key)}:</strong> {esc(value)}</li>")
            chunks.append("</ul>")
        rows = section.get("rows") or []
        if rows:
            columns = list(rows[0].keys())
            chunks.append("<table><thead><tr>" + "".join(f"<th>{esc(col)}</th>" for col in columns) + "</tr></thead><tbody>")
            for row in rows:
                chunks.append("<tr>" + "".join(f"<td>{esc(row.get(col))}</td>" for col in columns) + "</tr>")
            chunks.append("</tbody></table>")
        bullets = section.get("bullets") or []
        if bullets:
            chunks.append("<ul>" + "".join(f"<li>{esc(item)}</li>" for item in bullets) + "</ul>")
    chunks.append("<h2>Provenance manifest</h2><ul>")
    for item in source_manifest:
        chunks.append(
            f"<li><code>{esc(item.get('kind'))}</code> · <code>{esc(item.get('id'))}</code> · product <code>{esc(item.get('product_code'))}</code> · SHA-256 <code>{esc(item.get('checksum'))}</code></li>"
        )
    chunks.append("</ul></body></html>\n")
    return "".join(chunks)
