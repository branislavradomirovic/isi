from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TESTS = [
    "tests/test_isi_04c_public_portal_remediation.py",
    "tests/test_isi_04c_seo_routes.py",
    "tests/test_isi_04c_readiness_contract.py",
    "tests/test_isi_04c_public_template_labels.py",
    "tests/test_isi_27a_public_help_contract.py",
    "tests/test_isi_04b_public_experience.py",
    "tests/test_isi_04b_hotfix5_activity_catalog.py",
]


def main() -> int:
    analyzer = ROOT / "tools/qa/analyze_isi_public_portal_remediation.py"
    subprocess.run([sys.executable, str(analyzer)], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "-m", "pytest", "-q", *TESTS], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(analyzer)], cwd=ROOT, check=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
