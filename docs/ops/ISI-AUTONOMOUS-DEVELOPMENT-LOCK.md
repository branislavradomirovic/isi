# ISI Autonomous Development Lock

GitHub is the development control plane. The current ISI server is a deployment target only and is outside autonomous-development acceptance.

## Hard prohibitions

Autonomous agents and CI must not use SSH/SCP, invoke server deployment or release-deployment scripts, mutate DNS or central ingress, change production SMTP or Ollama configuration, or read/write production credentials, secrets, or institution data. Workflows receive no production secrets and use synthetic test values. Server tooling stays quarantined for the explicitly approved ISI-28 task.

Any server action, production credential use, release promotion, or deployment requires a separate owner-approved task. Ambiguity fails closed. Pull-request workflows never deploy, including for trusted branches.

## Status meanings

- `IMPLEMENTED`: code exists and local/task acceptance passes.
- `CI_VERIFIED`: required GitHub checks pass for the pull request.
- `SERVER_VERIFIED`: an explicitly approved server acceptance passed.
- `DEFERRED_SERVER_VERIFICATION`: implementation deliberately performed no server action.

Only evidence can advance status. ISI-17 ends with `DEFERRED_SERVER_VERIFICATION`; it cannot claim production verification.
