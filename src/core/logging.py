import logging

from src.core.config import get_settings
from src.platform.observability.logging import JsonFormatter


def configure_logging() -> None:
    settings = get_settings()
    level = getattr(logging, settings.isi_log_level.upper(), logging.INFO)

    # Configure the ISI logger explicitly. Using basicConfig alone is not
    # deterministic when Uvicorn, pytest, or another host already installed
    # root handlers before the application module is imported.
    isi_logger = logging.getLogger("isi")
    isi_logger.setLevel(level)
    isi_logger.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    isi_logger.addHandler(handler)
    isi_logger.propagate = False
