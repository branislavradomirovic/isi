# Dependency Lock Provenance

`requirements.lock` (CI/development) and `requirements.runtime.lock` (application image) were generated from `pyproject.toml` under CPython 3.11.15 with:

`python -m piptools compile --extra dev --strip-extras --output-file requirements.lock pyproject.toml`

`python -m piptools compile --strip-extras --output-file requirements.runtime.lock pyproject.toml`

Local, CI and container installation use the exact pins, followed by a no-dependency editable/package install so project metadata cannot re-resolve dependencies. Updates must regenerate and review both the manifest and lock.
