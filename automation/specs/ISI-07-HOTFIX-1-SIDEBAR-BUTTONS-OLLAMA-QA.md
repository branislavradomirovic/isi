# ISI-07 HOTFIX-1 — Sidebar Buttons + Local Ollama QA

## Status
Target phase: `ISI-07-SHARED-AI-FOUNDATION` while task remains `ready` after the successful ISI-07 main runner.

## Purpose
This hotfix closes three browser-QA findings without changing the ISI-07 database schema or domain scope:

1. the local QA launcher must open exactly one browser tab;
2. sidebar `radio` controls for product switching and navigation must be replaced by real Streamlit buttons;
3. local AI QA must exercise the real local Ollama gateway with one explicitly temporary foundation-test model.

## Temporary local QA model

`qwen2.5:7b-instruct`

The model is selected only as a temporary local foundation-QA chat model because it is already installed in the user's Ollama environment. Production/domain model selection is explicitly deferred to later SIMPA/ORDO AI phases.

The existing embedding registry remains unchanged. This hotfix does **not** pretend that one of the installed chat/VL models is an embedding model.

## UX contract
- No `st.sidebar.radio(...)` remains in the authenticated shell.
- SIMPA/ORDO product switching uses full-width/column buttons.
- Main sidebar navigation uses stacked buttons.
- Active product/navigation buttons use Streamlit's primary button state.
- Existing tenant/product/workspace selection semantics remain unchanged.

## Browser contract
The launcher starts Streamlit with `--server.headless true` and performs one explicit macOS `open` after readiness. Streamlit itself therefore does not open an additional tab.

## AI QA contract
The local QA launcher:
- retains the deterministic development stub only for the existing infrastructure/policy/namespace regression gate;
- sets the runtime default provider to `ollama`;
- updates the shared Ollama chat registry to `qwen2.5:7b-instruct`;
- requires local Ollama availability for this hotfix QA;
- performs one real ISI API AI job through `isi-ollama-chat-default`;
- requires the resulting provider to be `ollama` and the model to be `qwen2.5:7b-instruct`;
- requires valid structured diagnostic output;
- does not implement SIMPA or ORDO domain intelligence.

## Database
No migration. Alembic remains `20260828_0006`.

## Safety
- No automatic commit or push.
- No Docker PostgreSQL for local development.
- No external AI provider is introduced.
- Sensitive SIMPA requests remain forced through `local_only` policy and human review.
- AI remains decision support; human responsibility remains mandatory.
