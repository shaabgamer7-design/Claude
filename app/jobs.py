"""A single background worker: renders are CPU-bound, so one at a time is fastest."""
import queue
import threading
import time
import traceback
import uuid


class Job:
    def __init__(self, kind, title):
        self.id = uuid.uuid4().hex[:10]
        self.kind = kind
        self.title = title
        self.status = "queued"
        self.stage = "Waiting in queue"
        self.progress = 0.0
        self.result = None
        self.error = None
        self.created = time.time()
        self.started = None
        self.finished = None
        self._stage_base = 0.0
        self._stage_span = 1.0

    # Pipelines report progress per stage; `section` maps a stage's own 0..1
    # onto a slice of the overall bar.
    def section(self, start, end, stage=None):
        self._stage_base, self._stage_span = start, end - start
        if stage:
            self.stage = stage
        self.progress = max(self.progress, start)

    def set_progress(self, p):
        self.progress = max(self.progress,
                            min(0.999, self._stage_base + self._stage_span * max(0.0, min(1.0, p))))

    def set_stage(self, text):
        self.stage = text

    def to_dict(self):
        elapsed = (self.finished or time.time()) - self.started if self.started else 0
        eta = None
        if self.status == "running" and self.progress > 0.05:
            eta = elapsed * (1 - self.progress) / self.progress
        return {"id": self.id, "kind": self.kind, "title": self.title, "status": self.status,
                "stage": self.stage, "progress": round(self.progress, 4),
                "elapsed": round(elapsed, 1), "eta": round(eta, 1) if eta else None,
                "result": self.result, "error": self.error, "created": self.created}


class JobManager:
    def __init__(self):
        self.jobs = {}
        self.q = queue.Queue()
        self.lock = threading.Lock()
        threading.Thread(target=self._loop, daemon=True).start()

    def submit(self, kind, title, fn, *args, **kwargs):
        job = Job(kind, title)
        with self.lock:
            self.jobs[job.id] = job
        self.q.put((job, fn, args, kwargs))
        return job

    def get(self, job_id):
        return self.jobs.get(job_id)

    def recent(self, limit=20):
        with self.lock:
            jobs = sorted(self.jobs.values(), key=lambda j: j.created, reverse=True)
        return [j.to_dict() for j in jobs[:limit]]

    def _loop(self):
        while True:
            job, fn, args, kwargs = self.q.get()
            job.status, job.started = "running", time.time()
            job.stage = "Starting"
            try:
                job.result = fn(job, *args, **kwargs)
                job.status, job.progress, job.stage = "done", 1.0, "Finished"
            except Exception as exc:
                traceback.print_exc()
                job.status, job.error, job.stage = "error", str(exc), "Failed"
            finally:
                job.finished = time.time()
