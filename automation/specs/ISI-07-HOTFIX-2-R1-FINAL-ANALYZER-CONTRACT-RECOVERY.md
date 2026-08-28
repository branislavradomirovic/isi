# ISI-07 HOTFIX-2 R1 — Final Analyzer Contract Recovery

## Purpose
Recover the failed ISI-07 HOTFIX-2 runner after its regression test incorrectly depended on the formatting of a multiline `require(...)` call in `tools/audit_shared_ai_foundation.py`.

## Root cause
The HOTFIX-2 patch correctly replaced the stale `Development-only` static-audit token with the accepted local Ollama UI contract, but the accompanying regression test asserted the literal single-line text:

`require("src/streamlit_app/ai_workspace.py"`

The patch intentionally formatted that call over multiple lines, so the test failed even though the audit contract itself was correctly aligned.

## Scope
- Preserve the already accepted ISI-07 runtime, UI and local Ollama behavior.
- Preserve Alembic `20260828_0006`.
- Replace only the brittle HOTFIX-2 regression test with a formatting-independent semantic contract test.
- If the audit patch did not persist, apply the same accepted Ollama audit contract idempotently.
- Re-run static audit, focused ISI-07 tests and full regression suite.

## Non-goals
- No database migration.
- No AI provider/model behavior change.
- No Streamlit behavior change.
- No task-state change.
- No commit or push.

## Accepted audit contract
`tools/audit_shared_ai_foundation.py` must require the AI workspace to contain:
- `Shared AI Foundation`
- `Lokalni Ollama foundation test`
- `_render_local_ollama_diagnostic`
- `item.get("provider_type") == "ollama"`

and must not require the obsolete `Development-only` UI token.
