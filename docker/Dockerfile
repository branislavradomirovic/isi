ARG ISI_WOLFI_BASE=cgr.dev/chainguard/wolfi-base@sha256:9c2092b053779e14c82fb50f77b37bcc38b7d2c83972352d5813280f9d035b03
FROM ${ISI_WOLFI_BASE} AS python-base
RUN apk add --no-cache python-3.11=3.11.17-r1 ca-certificates-bundle=20260909-r2 tzdata=2026e-r0
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

FROM python-base AS builder
RUN apk add --no-cache py3.11-pip=26.2.1-r2
RUN python3.11 -m venv /opt/isi-venv
ENV PATH=/opt/isi-venv/bin:$PATH
COPY pyproject.toml requirements.runtime.lock README.md ./
COPY src ./src
RUN python -m pip install --no-cache-dir -r requirements.runtime.lock \
    && python -m pip install --no-cache-dir --no-deps . \
    && python -m pip check \
    && python -m pip uninstall -y pip setuptools wheel \
    && python -c "import importlib.metadata as m; assert not ({(d.metadata.get('Name') or '').lower() for d in m.distributions()} & {'pip', 'setuptools', 'wheel'})"

FROM python-base AS runtime
ARG ISI_GIT_SHA=development
ARG ISI_CANDIDATE_SHA=development
ARG ISI_RUNTIME_BASE_LOCK_SHA256=development
LABEL org.opencontainers.image.source="https://github.com/branislavradomirovic/isi" \
      org.opencontainers.image.revision="${ISI_GIT_SHA}" \
      org.isi.candidate.sha256="${ISI_CANDIDATE_SHA}" \
      org.isi.runtime-base.lock.sha256="${ISI_RUNTIME_BASE_LOCK_SHA256}"
ENV PATH=/opt/isi-venv/bin:$PATH
COPY --from=builder /opt/isi-venv /opt/isi-venv
COPY . .
