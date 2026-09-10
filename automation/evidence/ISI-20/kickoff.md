# ISI-20 Kickoff

Task: `ISI-20-ENTERPRISE-SECURITY-COMPLETION`

Baseline: `4713a1deb7ccec0b99b92985424693a50727a1f6`

Dependency evidence: ISI-19 merged as the baseline above and post-merge GitHub Actions run #51 / `34502016805` completed successfully.

State: `SPEC_READY`

Implementation branch: `automation/isi-20-enterprise-security`

Tracking issue: #9.

Scope: provider-neutral MFA/challenge readiness, authentication assurance/step-up for privileged operations, safe session/device inventory and revocation, expanded privacy-safe security events, access/entitlement/workspace negative tests and a CI-safe penetration-test readiness pack.

Existing controls are extended, not replaced: `AuthSession`, login throttling, privacy hashing, `SecurityEvent`, role/permission/product entitlement model, organization administration/audit and last-admin safeguards.

Server verification: `DEFERRED_SERVER_VERIFICATION`. No current-server security scan, deployment, SSH/SCP, DNS/ingress, production SMTP, production secrets/data or server Ollama work is authorized before ISI-28.
