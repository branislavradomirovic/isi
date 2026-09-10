# Dependency Lock Provenance

`requirements.lock` (CI/development) and `requirements.runtime.lock` (application image) were generated from `pyproject.toml` under CPython 3.11.15 using `pip-tools==7.6.1`:

`python -m pip install pip-tools==7.6.1`

`python -m piptools compile --extra dev --strip-extras --output-file requirements.lock pyproject.toml`

`python -m piptools compile --strip-extras --output-file requirements.runtime.lock pyproject.toml`

The PEP-517 bootstrap is also deterministic: `pyproject.toml` pins `setuptools==84.0.0` and `wheel==0.48.0` exactly. These build requirements are intentionally separate from the application/runtime lock because isolated PEP-517 builds resolve them before project installation.

Local, CI and container installation use the exact application pins, followed by a no-dependency editable/package install so project metadata cannot re-resolve application dependencies. Dependency updates must regenerate and review both lock files and the exact PEP-517 bootstrap pins.
