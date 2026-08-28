# ADR-0024 - ISI target-server production topology

Status: accepted for ISI-15/ISI-16 implementation.

## Observed target server

The read-only preflight and edge audit on 2026-08-28 established the deployment target:

- Ubuntu 24.04.4 LTS, 2 vCPU, 15 GiB RAM.
- Docker Engine 29.6.0 and Docker Compose 5.1.4.
- Existing Compose projects: `app` (OralScan), `krcuga`, and `central-ingress`.
- `central-ingress` owns public TCP/443 and maps it to nginx port 8443.
- Krcuga is currently routed to host port 8501; OralScan is routed to host port 8502.
- Host Caddy remains active for the separate OralScan 8444 route.
- Shared host Ollama is reachable on 11434 and already contains the approved server models.
- `isi.rs` and `www.isi.rs` still resolve to 79.175.68.5, not this target server. DNS is therefore an ISI-16 cutover action.
- Host port 8445 was free at audit time and is reserved only as a loopback pre-cutover acceptance endpoint.
- Approximately 16 GiB filesystem space was free. No Docker prune is part of ISI deployment.

## Decision

ISI is an independent Compose project named `isi` rooted operationally at `/home/ubuntu/ISI`.

Stateful services owned by ISI:

- PostgreSQL 17;
- Redis 7;
- MinIO/S3-compatible object storage;
- API;
- Streamlit `/app` UI;
- `isi-data` RQ worker;
- `isi-ai` RQ worker.

ISI does not run an Ollama container. Application containers reach the existing host runtime through `host.docker.internal:11434` with the Linux `host-gateway` mapping.

PostgreSQL, Redis, MinIO, API, and Streamlit are not published on public host ports. The only pre-cutover host binding is `127.0.0.1:8445` for the temporary ISI nginx acceptance edge.

API and Streamlit also attach to a dedicated external Docker network `isi_ingress`, using aliases `isi-api` and `isi-streamlit`. `central-ingress` is not attached to this network until ISI-16. ISI-16 will extend the central-ingress Compose configuration, with backup and rollback, rather than attach ISI directly to the central-ingress project's managed default network.

## Pre-cutover data isolation

Server acceptance uses:

- PostgreSQL database `isi_preproduction`;
- Redis database index 1;
- MinIO bucket `isi-preproduction`;
- internal Mailpit SMTP capture.

This allows full automated server acceptance without contaminating the eventual production database, Redis namespace, object bucket, or external mail channel.

ISI-16 creates/promotes to fresh production state:

- PostgreSQL database `isi`;
- Redis database index 0;
- MinIO bucket `isi-production`;
- real production SMTP;
- public TLS and central-ingress route;
- DNS cutover for `isi.rs` / `www.isi.rs`.

## Non-goals in ISI-15

ISI-15 does not change public DNS, obtain or activate a public production certificate, modify production SMTP recipients, publish draft legacy pages, or route public traffic to ISI.
