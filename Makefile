PYTHON ?= .venv/bin/python

.PHONY: install test compile lint typecheck analyze acceptance api streamlit compose-config up down

install:
	python3 -m venv .venv
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.lock
	$(PYTHON) -m pip install --no-deps -e .

test:
	$(PYTHON) -m pytest -q

compile:
	$(PYTHON) -m compileall -q src tests

lint:
	$(PYTHON) -m ruff check --select E9 src tests
	$(PYTHON) -m ruff check tools/ci tests/test_isi_17_harness_contract.py

typecheck:
	$(PYTHON) -m mypy

analyze: compile lint typecheck test
	git diff --check

acceptance:
	./tools/ci/run_isi17_acceptance.sh

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
