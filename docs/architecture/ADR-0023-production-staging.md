# ADR-0023 - Production staging topology

## Decision
ISI-15 uses a dedicated Compose staging topology rather than converting the local-development Compose file into production behavior.

The browser-facing boundary is nginx over local TLS. FastAPI remains the authority for public/API behavior and authorization, Streamlit remains the authenticated presentation layer, PostgreSQL remains the durable relational source of truth, Redis/RQ remains the background job path, and raw uploaded bytes use the existing S3-compatible storage boundary.

A pinned legacy MinIO server is used only as a local S3-compatible staging harness. Mailpit is used only as a local SMTP capture sink. Neither choice binds ISI-16 to those products.

## Rationale
Development must continue to use the stable native PostgreSQL workflow. Staging must prove container migration, queueing, storage, reverse-proxy, TLS, SMTP and disaster-recovery behavior without touching that development database or any production resource.

## Safety
- Staging binds browser and Mailpit ports to loopback by default.
- Database, Redis and object-storage ports are not published to the host.
- Secrets and local certificates are generated outside the repository.
- Staging is `noindex` at nginx.
- Restore rehearsal uses a second Compose project.
- No production cutover is part of this ADR.
