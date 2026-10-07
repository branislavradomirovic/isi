# ISI Development Workstation Requirements

## Authority

This document is the machine-level dependency authority for local ISI development. Any new system/workstation dependency must be documented here and in `docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md` before installation.

## Supported owner workstations

- MacBook Air
- iMac
- macOS
- exactly one active ISI development workstation at a time

## Source handoff contract

GitHub `origin/main` is the only source-code handoff authority between Macs.

Source handoff requires:

- branch `main`;
- local `HEAD == origin/main`;
- clean staged/unstaged/untracked state;
- empty stash;
- exactly one development worktree.

The destination fetches and fast-forwards to the exact accepted `origin/main` SHA before development.

Never copy between Macs:

- `.venv` or another virtual environment;
- `.env` or secrets;
- PostgreSQL/Redis/Docker state;
- logs or caches;
- Codex/GitHub/SSH credentials.

## Required tools

- Git
- GitHub CLI with repository access
- Python 3.11 (project supports >=3.11,<3.13; canonical development/CI baseline is 3.11)
- PostgreSQL 17 for native PostgreSQL development/acceptance
- standard `codex` CLI for Codex-backed implementation, authenticated by the operator to `branislav.radomirovic@outlook.com`

## Conditional tools

- Docker/Compose for container/compose acceptance and explicitly requested container workflows.
- Redis when exercising runtime paths that require the configured Redis/RQ infrastructure locally.

## Python environment

Use the repository lock authority:

```bash
make install
```

This creates `.venv`, installs `requirements.lock`, and installs the project without resolving a second dependency graph. Do not copy an environment from another Mac.

## Codex

Active policy:

```text
CLI: codex
Account: branislav.radomirovic@outlook.com
codex-isi wrapper: legacy / not required
Project-specific CODEX_HOME: legacy / not required
```

Project boundaries remain enforced by the Master Plan, AGENTS.md, locked task MD, runner, independent analyzer, exact mutable surface and human review. Codex credentials remain machine-local.

## Hosted CI

The full `ISI required acceptance` workflow remains manual `workflow_dispatch` only during active development. Ordinary development pushes do not authorize full hosted acceptance.

## Current iMac audited baseline — 2026-09-19

- macOS 15.8, x86_64
- MacPorts 2.12.6
- Git 2.55.0
- GitHub CLI 2.100.0 with SSH Git access
- Python 3.11.16
- Docker 29.8.0
- Docker Compose 5.5.1
- PostgreSQL 17.11
- standard Codex CLI 0.154.0
- native Redis not installed at audit time; install only after a concrete ISI local-runtime requirement is approved and documented

## ISI-27C release tooling

Portable source packaging uses existing Python 3.11 standard-library hashing, tar
inspection and deterministic gzip plus Git. Signing/verification requires existing
OpenSSH 8.2+ with ssh-keygen -Y and the existing owner GitHub identity in the local
SSH agent. No private key is copied to GitHub or between Macs. Docker supplies
image build and the disposable official Trivy 0.75.0 scanner; hosted CI uses the
pinned official action. No new workstation package is installed by this slice.


## ISI-29B GIS dependency decision — 2026-10-07

Local feature contract permits pinned Shapely 2.1.2 for bounded geometry topology validation. Existing NumPy retained; binary wheel only, no host GEOS/GDAL/PROJ install. Official requirements Python>=3.10 and platform wheels support canonical Python3.11/macOS and musllinux x86_64 runtime; actual compatibility is an acceptance gate. Shapely BSD3 and bundled GEOS LGPL2.1 notices remain supply-chain obligations. No CRS reprojection, geocoder, tiles or PostGIS. Source: https://shapely.readthedocs.io/en/2.1.2/installation.html . No installation or deployment verified by this planning record.
