# Enabled ISI-17 Gates

`.github/workflows/ci.yml` runs on pull requests and relevant pushes with read-only repository permissions. Its required groups are: `policy`, `quality`, `tests`, `architecture-security`, `migration`, `compose`, `supply-chain`, `build`, and aggregate `acceptance`.

Supply-chain policy blocks every vulnerability reported by pip-audit, Bandit findings of high severity with medium-or-higher confidence, and verified Gitleaks findings. Container build does not push or deploy.
