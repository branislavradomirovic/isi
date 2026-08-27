# ISI Platform

Foundation repository for the Institut za socijalnu inkluziju technology platform.

Architecture baseline:

- FastAPI/Jinja public institutional website
- Streamlit authenticated application
- shared FastAPI backend
- PostgreSQL
- Redis/RQ
- separate SIMPA and ORDO domain boundaries

This repository is currently in **ISI-00/01 Foundation**. It intentionally contains no production SIMPA or ORDO business functionality and no final `isi.rs` design.

## Local setup

```bash
cp .env.example .env
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
pytest -q
```

Run public/API app:

```bash
.venv/bin/python -m uvicorn src.api.app:app --reload --port 8000
```

Run private Streamlit placeholder:

```bash
.venv/bin/python -m streamlit run src/streamlit_app/app.py --server.port 8501
```

Docker:

```bash
docker compose up --build
```

## Current domain boundaries

- `src/domains/simpa/`
- `src/domains/ordo/`

Shared code must not absorb domain-specific indicators, analytical logic, or prompts.
