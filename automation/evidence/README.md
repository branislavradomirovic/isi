# Task Evidence Contract

Each task stores durable, reviewable evidence in `automation/evidence/<TASK-ID>/`. Text, JSON, JUnit XML and concise logs are preferred. Generated evidence must be reproducible and should not contain machine-specific noise.

At minimum record the baseline and final task commit, exact commands, outcome and test count/summary, migration state or `not applicable`, warnings, deferred server checks, and pull-request/review state. Identify the workflow and gate versions used. A failing gate remains a failure.

Never record production secrets, credentials, authorization headers, cookies, passwords, raw invitation/reset/session tokens, sensitive institution data, unnecessary PII, or production configuration values. Redact before committing; when safe redaction is uncertain, omit the value and describe only its category.

Evidence supports but does not replace authoritative GitHub checks. Update commit/PR fields after those identities exist without claiming `CI_VERIFIED` before all required checks pass.
