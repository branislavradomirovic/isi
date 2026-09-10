# ISI-19 Recovery Rehearsal Evidence

Implementation code head: `dd0cf78a48afcb984aadd74a4808e48d4d739a65`

GitHub Actions: run #49 / `34500748759` — `success`.

Native PostgreSQL job: `102950626585` — `success`.

Observed recovery result:

`ISI-19 RECOVERY PASS: PostgreSQL 17 and scoped object storage restored and verified`

The rehearsal migrated a synthetic PostgreSQL 17 source to the current Alembic head, inserted isolated SIMPA/ORDO fixture rows, created scoped SIMPA/ORDO local object-storage fixtures, created a custom-format PostgreSQL dump, restored it to a fresh PostgreSQL 17 target, re-checked the migration head, verified the exact relational fixtures, restored the object keys and verified exact object bytes.

The native PostgreSQL job subsequently reported its complete gate success and uploaded artifact ID `10161771050`. GitHub reported the uploaded ZIP SHA-256 as `6d23ae92c3767e77651e5f84d36b55797985602e6b7ab2d9868d760b5cc39f2d`.

No current-server target, production backup media, production credentials, SSH/SCP, DNS/ingress, production SMTP or server Ollama was used. Server verification remains `DEFERRED_SERVER_VERIFICATION`.
