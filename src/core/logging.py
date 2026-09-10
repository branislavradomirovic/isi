import logging

from src.core.config import get_settings
from src.platform.observability.logging import JsonFormatter


def configure_logging() -> None:
    settings = get_settings()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(
        level=getattr(logging, settings.isi_log_level.upper(), logging.INFO),
        handlers=[handler],
    )
