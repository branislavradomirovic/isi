from __future__ import annotations

from pathlib import Path
import tomllib


def test_statsmodels_is_the_only_new_direct_runtime_dependency_family():
    project = tomllib.loads(Path("pyproject.toml").read_text())["project"]
    dependencies = project["dependencies"]
    assert "statsmodels>=0.14.6,<0.16" in dependencies
    lowered = [item.casefold() for item in dependencies]
    assert not any(item.startswith("numpy") for item in lowered)
    assert not any(item.startswith("pandas") for item in lowered)
    assert not any(item.startswith("scipy") for item in lowered)
    assert not any(item.startswith("scikit-learn") for item in lowered)
    assert not any(item.startswith("pip-tools") for item in lowered)


def test_canonical_lock_contains_resolved_statsmodels_stack_and_header():
    lock = Path("requirements.lock").read_text()
    assert "pip-compile --extra=dev --output-file=requirements.lock --strip-extras pyproject.toml" in lock
    for package in ("statsmodels==", "scipy==", "patsy==", "numpy==", "pandas=="):
        assert package in lock
    assert "scikit-learn==" not in lock
    assert "pip-tools==" not in lock
    statsmodels_block = lock[lock.index("statsmodels==") :]
    assert "# via isi-platform (pyproject.toml)" in statsmodels_block[:300]


def test_new_source_imports_statsmodels_but_not_transitive_numeric_packages_directly():
    engine = Path("src/domains/simpa/statistical_models.py").read_text()
    contracts = Path("src/domains/simpa/statistical_contracts.py").read_text()
    assert "import statsmodels" in engine
    for forbidden in ("import numpy", "from numpy", "import pandas", "from pandas", "import scipy", "from scipy"):
        assert forbidden not in engine
        assert forbidden not in contracts
