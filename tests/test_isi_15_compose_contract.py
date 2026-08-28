from pathlib import Path


def test_staging_compose_is_isolated_and_production_shaped():
    text = Path("docker-compose.staging.yml").read_text()
    for service in ("postgres:", "redis:", "minio:", "mailpit:", "migrate:", "api:", "streamlit:", "data-worker:", "ai-worker:", "nginx:"):
        assert service in text
    assert '127.0.0.1:${ISI15_HTTPS_PORT' in text
    assert '127.0.0.1:${ISI15_MAILPIT_UI_PORT' in text
    assert '"5432:5432"' not in text
    assert '"6379:6379"' not in text
    assert "python\", \"-m\", \"src.workers.data_worker" in text
    assert "python\", \"-m\", \"src.workers.ai_worker" in text
    assert "alembic\", \"upgrade\", \"head" in text


def test_nginx_tls_streamlit_websocket_and_noindex_contract():
    text = Path("docker/nginx/isi15-staging.conf").read_text()
    assert "listen 443 ssl" in text
    assert "location /app/" in text
    assert "proxy_set_header Upgrade $http_upgrade" in text
    assert "X-Robots-Tag" in text
    assert "Disallow: /" in text
