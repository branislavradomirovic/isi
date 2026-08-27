PYTHON ?= .venv/bin/python

.PHONY: install test compile analyze api streamlit compose-config up down

install:
	python3 -m venv .venv
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e '.[dev]'

test:
	$(PYTHON) -m pytest -q

compile:
	$(PYTHON) -m compileall -q src tests

analyze: compile test
	@git diff --check 2>/dev/null || true

api:
	$(PYTHON) -m uvicorn src.api.app:app --reload --port 8000

streamlit:
	$(PYTHON) -m streamlit run src/streamlit_app/app.py --server.port 8501

compose-config:
	docker compose config

up:
	docker compose up --build

down:
	docker compose down
