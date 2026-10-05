from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_HISTORICAL_FINDINGS = {
    "c177f9d705efd6f68d95ef7d13847b03a8e19229:docs/legal/ISI-LEGAL-NOTICES-RELEASE-CHECKLIST.md:generic-api-key:27",
    "7e11ee2a6f7546eacc3207e15cacfc35f6d04f3e:tests/test_isi_25b_governance_contract.py:generic-api-key:33",
    "e4b5b7f5927bc553fd616800d37beb5d115bb46e:automation/specs/ISI-26-R1-HISTORICAL-GOVERNANCE-EVIDENCE.json:generic-api-key:24",
    "ae28c00cee74b7a3e05d1ba5aaea0c32cb1a18bf:automation/evidence/ISI-20/acceptance-summary.md:generic-api-key:9",
    "f4b3a3c2486a2d3a051a70d582245e199d1b36ba:automation/evidence/ISI-20/penetration-test-readiness.md:generic-api-key:34",
    "ae28c00cee74b7a3e05d1ba5aaea0c32cb1a18bf:docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md:generic-api-key:217",
    "3fa133c93fa752b325fec84859931b159264c55d:tests/test_isi_15_runtime_config.py:generic-api-key:16",
    "3fa133c93fa752b325fec84859931b159264c55d:tools/staging/probe_smtp.py:generic-api-key:30",
    "3fa133c93fa752b325fec84859931b159264c55d:tools/staging/probe_smtp.py:generic-api-key:32",
    "3fa133c93fa752b325fec84859931b159264c55d:tests/test_isi_server_runtime_promotion.py:generic-api-key:16",
    "503765191e8bea26e000bc4c4e4f582ac7026203:tests/test_isi_02b_security.py:generic-api-key:7",
}


def test_gitleaks_baseline_is_exact_and_limited_to_reviewed_history():
    entries = {
        line.strip()
        for line in (ROOT / ".gitleaksignore").read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert entries == EXPECTED_HISTORICAL_FINDINGS
    assert len(entries) == 11
    assert all(
        re.fullmatch(r"[0-9a-f]{40}:[A-Za-z0-9_./-]+:generic-api-key:[0-9]+", entry)
        for entry in entries
    )
