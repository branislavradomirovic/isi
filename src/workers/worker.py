from redis import Redis
from rq import Worker

from src.core.config import get_settings


def main() -> None:
    settings = get_settings()
    connection = Redis.from_url(settings.redis_url)
    worker = Worker(["default"], connection=connection)
    worker.work(with_scheduler=False)


if __name__ == "__main__":
    main()
