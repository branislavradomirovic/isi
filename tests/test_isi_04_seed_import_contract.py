import importlib
from pathlib import Path


def test_seed_service_lives_in_installable_src_package():
    module = importlib.import_module("src.public.platform_seed")
    assert callable(module.seed_platform_pages)


def test_cli_is_thin_wrapper_over_seed_service():
    text = Path("tools/seed_public_platform_pages.py").read_text()
    assert "from src.public.platform_seed import seed_platform_pages" in text
    assert "def seed(" not in text
