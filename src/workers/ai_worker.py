from __future__ import annotations

from redis import Redis
from rq import Queue, Worker

from src.core.config import get_settings


def main() -> None:
    settings = get_settings()
    connection = Redis.from_url(settings.redis_url)
    worker = Worker([Queue("isi-ai", connection=connection)], connection=connection)
    worker.work()


if __name__ == "__main__":
    main()
