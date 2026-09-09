from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Lock
from uuid import uuid4

class JobStore:
    def __init__(self, product):
        self.product = product
        self.jobs = {}
        self.lock = Lock()
        self.pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="bie-job")

    def submit(self, source_path, task="book_to_video_code"):
        job_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self.lock:
            self.jobs[job_id] = {"job_id": job_id, "status": "queued", "created_at": now}
        self.pool.submit(self._run, job_id, source_path, task)
        return self.jobs[job_id]

    def _run(self, job_id, source_path, task):
        self._update(job_id, status="running")
        try:
            result = self.product.process(source_path, task)
            self._update(job_id, status="completed", result=result)
        except Exception as exc:
            self._update(job_id, status="failed", error={"type": type(exc).__name__, "message": str(exc)})

    def _update(self, job_id, **values):
        with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id].update(values)

    def get(self, job_id):
        with self.lock:
            return self.jobs.get(job_id)
