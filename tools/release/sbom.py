"""Deterministic CycloneDX for pinned locks; installed image SBOM is separate."""

from __future__ import annotations

import hashlib
import re
import uuid
from pathlib import Path
from urllib.parse import quote

REPOSITORY = "https://github.com/branislavradomirovic/isi"


def sha256_file(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            result.update(chunk)
    return result.hexdigest()


def lock_sbom(root: Path, sha: str) -> dict:
    components: dict[str, dict] = {}
    for filename in ("requirements.lock", "requirements.runtime.lock"):
        path = root / filename
        count = 0
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([A-Za-z0-9_.+!-]+)", line)
            if not match:
                raise ValueError(f"Unpinned or unsupported lock line: {filename}")
            name = re.sub(r"[-_.]+", "-", match[1]).lower()
            version = match[2]
            reference = f"pkg:pypi/{name}@{quote(version, safe='')}"
            component = components.setdefault(
                reference,
                {
                    "type": "library",
                    "name": name,
                    "version": version,
                    "purl": reference,
                    "bom-ref": reference,
                    "properties": [],
                },
            )
            if any(
                item["name"] == "isi:dependency-lock" and item["value"] == filename for item in component["properties"]
            ):
                raise ValueError("duplicate_lock_component")
            component["properties"].append({"name": "isi:dependency-lock", "value": filename})
            count += 1
        if not count:
            raise ValueError("empty_dependency_lock")
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "version": 1,
        "serialNumber": "urn:uuid:" + str(uuid.uuid5(uuid.NAMESPACE_URL, REPOSITORY + "/" + sha + "/locks")),
        "metadata": {
            "component": {
                "type": "application",
                "name": "isi-platform",
                "version": sha,
                "bom-ref": REPOSITORY + "@" + sha,
            },
            "properties": [
                {"name": "isi:scope", "value": "declared pinned locks; installed image SBOM supplied separately"},
                {"name": "isi:runtime-base-lock-sha256", "value": sha256_file(root / "docker/runtime-base.lock.json")},
                *[
                    {"name": f"isi:sha256:{name}", "value": sha256_file(root / name)}
                    for name in ("requirements.lock", "requirements.runtime.lock")
                ],
            ],
        },
        "components": [components[key] for key in sorted(components)],
    }


def validate_sbom(document: dict) -> None:
    if document.get("bomFormat") != "CycloneDX" or document.get("specVersion") not in {"1.5", "1.6", "1.7"}:
        raise ValueError("unsupported_sbom_format")
    components = document.get("components")
    if not isinstance(components, list) or not components:
        raise ValueError("empty_sbom")
    if any(not component.get("name") or not component.get("version") for component in components):
        raise ValueError("incomplete_sbom_component")
