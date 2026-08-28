from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def service_block(text: str, name: str) -> str:
    marker = f"  {name}:\n"
    start = text.index(marker) + len(marker)
    match = re.search(r"(?m)^  [A-Za-z0-9_-]+:\n", text[start:])
    end = len(text) if match is None else start + match.start()
    return text[start:end]


def test_server_compose_isolated_from_existing_host_ports_and_ollama():
    text = (ROOT / "docker-compose.server.yml").read_text()
    assert "  ollama:\n" not in text
    assert "pg_isready -h 127.0.0.1 -U $${POSTGRES_USER} -d $${POSTGRES_DB}" in service_block(text, "postgres")
    for name in ("postgres", "redis", "minio", "api", "streamlit", "data-worker", "ai-worker"):
        assert "\n    ports:" not in service_block(text, name)
    edge = service_block(text, "edge")
    assert '"127.0.0.1:${ISI_PRECUTOVER_HTTPS_PORT:-8445}:443"' in edge
    assert 'profiles: ["precutover"]' in edge
    assert 'profiles: ["precutover"]' in service_block(text, "mailpit")
    edge_conf = (ROOT / "docker/nginx/isi-server-precutover.conf").read_text()
    assert 'add_header X-Robots-Tag "noindex, nofollow, noarchive" always;' in edge_conf
    assert r'return 200 "User-agent: *\nDisallow: /\n";' in edge_conf
    assert 'proxy_set_header Host localhost;' in edge_conf
    assert "resolver 127.0.0.11 valid=5s ipv6=off;" in edge_conf
    assert "resolver_timeout 2s;" in edge_conf
    assert "set $api_upstream api:8000;" in edge_conf
    assert "set $streamlit_upstream streamlit:8501;" in edge_conf
    assert "proxy_pass http://$api_upstream;" in edge_conf
    assert "proxy_pass http://$streamlit_upstream;" in edge_conf
    assert "proxy_pass http://api:8000;" not in edge_conf
    assert "proxy_pass http://streamlit:8501;" not in edge_conf


def test_precutover_edge_canonicalizes_overlapping_security_headers():
    text = (ROOT / "docker/nginx/isi-server-precutover.conf").read_text()
    for header in (
        "Strict-Transport-Security",
        "X-Content-Type-Options",
        "Referrer-Policy",
        "X-Frame-Options",
    ):
        assert f"add_header {header} " in text
        assert f"proxy_hide_header {header};" in text


def test_server_compose_uses_dedicated_ingress_network_and_stable_aliases():
    text = (ROOT / "docker-compose.server.yml").read_text()
    assert "name: ${ISI_INGRESS_NETWORK:-isi_ingress}" in text
    assert "external: true" in text
    assert 'aliases: ["isi-api"]' in service_block(text, "api")
    assert 'aliases: ["isi-streamlit"]' in service_block(text, "streamlit")
    assert '"host.docker.internal:host-gateway"' in text


def test_preproduction_runtime_is_separate_from_future_production_state():
    text = (ROOT / ".env.server.example").read_text()
    assert "POSTGRES_DB=isi_preproduction" in text
    assert "REDIS_URL=redis://redis:6379/1" in text
    assert "DATA_S3_BUCKET=isi-preproduction" in text
    assert "SMTP_HOST=mailpit" in text
    assert "AI_OLLAMA_BASE_URL=http://host.docker.internal:11434" in text
    assert "POSTGRES_PASSWORD=GENERATE_ON_SERVER" in text


def test_central_ingress_fragment_is_dormant_isi16_template():
    text = (ROOT / "deploy/central-ingress/isi-production-server.conf.fragment").read_text()
    assert "ISI-16 template" in text
    assert "listen 8443 ssl;" in text
    assert "server_name isi.rs www.isi.rs;" in text
    assert "resolver 127.0.0.11 valid=5s ipv6=off;" in text
    assert "resolver_timeout 2s;" in text
    assert "set $isi_api_upstream isi-api:8000;" in text
    assert "set $isi_streamlit_upstream isi-streamlit:8501;" in text
    assert "proxy_pass http://$isi_api_upstream;" in text
    assert "proxy_pass http://$isi_streamlit_upstream;" in text
    assert "proxy_pass http://isi-api:8000;" not in text
    assert "proxy_pass http://isi-streamlit:8501;" not in text
    assert "/etc/nginx/isi-certs/fullchain.pem" in text


def test_backup_restore_rehearsal_has_bounded_readiness_and_diagnostics():
    text = (ROOT / "tools/server/backup_restore_rehearsal.sh").read_text()
    assert "for _ in $(seq 1 180); do" in text
    assert text.count("pg_isready -h 127.0.0.1 -U") == 2
    assert "ERROR isolated restore PostgreSQL did not become ready" in text
    assert "logs --tail=120 postgres" in text
    assert "PASS isolated restore PostgreSQL ready" in text
    assert "ERROR isolated restore MinIO initialization failed" in text
    assert "logs --tail=120 minio" in text
    assert "PASS isolated restore MinIO ready" in text


def test_release_workflow_is_git_archive_and_locked_target():
    build = (ROOT / "tools/release/build_server_release.sh").read_text()
    deploy = (ROOT / "tools/release/deploy_server_release.sh").read_text()
    assert "git archive" in build
    assert "git status --porcelain" in build
    assert "git commit" not in build
    assert "git push" not in build
    assert "git reset" not in build
    assert "git clean" not in build
    assert 'HOST="${ISI_TARGET_HOST:-94.230.189.146}"' in deploy
    assert 'PORT="${ISI_SSH_PORT:-222}"' in deploy
    assert "target is locked to ubuntu@94.230.189.146:222" in deploy
    assert "docker system prune" not in deploy
