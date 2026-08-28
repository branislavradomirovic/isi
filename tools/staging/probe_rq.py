from __future__ import annotations

import time
import uuid

from redis import Redis
from rq import Queue
from rq.job import Job

from src.core.config import get_settings


def main() -> int:
    settings = get_settings()
    connection = Redis.from_url(settings.redis_url)
    for queue_name in ("isi-data", "isi-ai"):
        label = f"isi15-{queue_name}-{uuid.uuid4().hex[:8]}"
        queue = Queue(queue_name, connection=connection)
        job = queue.enqueue("tools.staging.rq_probe_jobs.probe", label, job_timeout=30, result_ttl=120)
        deadline = time.time() + 30
        while time.time() < deadline:
            job = Job.fetch(job.id, connection=connection)
            status = job.get_status(refresh=True)
            if status == "finished":
                assert job.result == {"status": "ok", "label": label}
                print(f"PASS RQ {queue_name} -> finished")
                break
            if status in {"failed", "stopped", "canceled"}:
                raise RuntimeError(f"RQ probe failed on {queue_name}: {status}")
            time.sleep(0.25)
        else:
            raise TimeoutError(f"RQ probe timed out on {queue_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
