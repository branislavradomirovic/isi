"""Build deterministic, offline media fixtures for native PostgreSQL CI tests."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path

import httpx

from src.core.database import build_engine, build_session_factory
from src.public_migration.media_redirect_validation import (
    ALLOWED_MEDIA_HOSTS,
    build_acceptance_report,
    download_media_assets,
    finalize_redirect_plan,
    normalize_draft_links,
)


def _offline_media_response(request: httpx.Request) -> httpx.Response:
    host = (request.url.host or "").lower()
    if host not in ALLOWED_MEDIA_HOSTS:
        raise RuntimeError(f"offline fixture rejected non-ISI media host: {host}")
    source = str(request.url)
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    payload = f"ISI native PostgreSQL offline media fixture\n{source}\n{digest}\n".encode()
    return httpx.Response(
        200,
        headers={"content-type": "application/octet-stream"},
        content=payload,
        request=request,
    )


def main() -> int:
    report_root = Path(os.environ.get("ISI_NATIVE_FIXTURE_REPORT_ROOT", "test-results/native-postgres/legacy"))
    storage_root = Path(os.environ.get("ISI_NATIVE_MEDIA_ROOT", "test-results/native-postgres/media"))
    if storage_root.exists():
        shutil.rmtree(storage_root)
    report_root.mkdir(parents=True, exist_ok=True)
    storage_root.mkdir(parents=True, exist_ok=True)

    factory = build_session_factory(build_engine())
    transport = httpx.MockTransport(_offline_media_response)
    with httpx.Client(transport=transport, follow_redirects=True) as client:
        with factory() as session:
            media_manifest = download_media_assets(
                session,
                storage_root=storage_root,
                manifest_path=report_root / "media_manifest.json",
                client=client,
            )
            session.commit()

    with factory() as session:
        link_report = normalize_draft_links(session, report_path=report_root / "link_normalization_report.json")
        if link_report["unresolved_internal"]:
            session.rollback()
            raise RuntimeError("offline native PostgreSQL fixture has unresolved internal links")
        redirect_report = finalize_redirect_plan(session, csv_path=report_root / "final_redirect_map.csv")
        session.commit()

    with factory() as session:
        acceptance = build_acceptance_report(
            session,
            storage_root=storage_root,
            media_manifest_path=report_root / "media_manifest.json",
            link_report_path=report_root / "link_normalization_report.json",
            final_redirect_csv=report_root / "final_redirect_map.csv",
            output_path=report_root / "migration_acceptance_report.json",
        )

    summary = {
        "offline": True,
        "network_requests": 0,
        "assets_total": media_manifest["assets_total"],
        "redirects": redirect_report,
        "acceptance_passed": acceptance["acceptance_passed"],
    }
    (report_root / "fixture-summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if not acceptance["acceptance_passed"]:
        raise RuntimeError("offline native PostgreSQL media fixture failed acceptance")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
