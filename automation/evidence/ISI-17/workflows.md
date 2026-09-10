# Enabled ISI-17 Gates

`.github/workflows/ci.yml` runs on pull requests and relevant pushes with least-privilege repository permissions (`contents: read`, `pull-requests: read`). Its required groups are: `policy`, `quality`, `tests`, `architecture-security`, `migration`, `native-postgres`, `compose`, `supply-chain`, `build`, and aggregate `acceptance`.

The `native-postgres` gate provisions an ephemeral PostgreSQL 17 service, reconstructs committed legacy/public fixtures, uses an in-process `httpx.MockTransport` for media, and executes the complete native PostgreSQL regression set without production/server I/O.

Supply-chain policy blocks every vulnerability reported by pip-audit, Bandit findings of high severity with medium-or-higher confidence, and verified Gitleaks findings. Container build does not push or deploy. The aggregate `acceptance` job fails unless every required gate succeeds.
