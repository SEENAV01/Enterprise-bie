"""Continuous LOCAL apps/api /v1/jobs worker; never an operator executor."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import math
from pathlib import Path
import re
import signal
import threading

from apps.api.job_service import PdfInspectionJobService, data_root_from_env

DEFAULT_POLL_INTERVAL = 1.0
MIN_POLL_INTERVAL = 0.1
MAX_POLL_INTERVAL = 60.0


class WorkerServiceError(RuntimeError):
    """Safe process-level failure, distinct from a governed FAILED document."""


def validate_poll_interval(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("invalid_poll_interval")
    if not math.isfinite(value) or not MIN_POLL_INTERVAL <= value <= MAX_POLL_INTERVAL:
        raise ValueError("invalid_poll_interval")
    return float(value)


def api_worker_root(root: Path | None = None) -> Path:
    """Reject known operator roots and their per-run descendants before opening stores.

    This prevents accidental namespace crossover. It is not an authorization
    boundary against an OS administrator who can relocate/rewrite the stores.
    No operator module is imported and no operator database is opened.
    """
    resolved = (Path(root) if root is not None else data_root_from_env()).resolve()
    for parent in (resolved, *resolved.parents):
        if (parent / "operator.sqlite3").exists() or (parent / "operator.sqlite3").is_symlink():
            raise WorkerServiceError("operator_namespace_forbidden")
    return resolved


@contextmanager
def stop_signals(stop: threading.Event):
    """Set a cooperative flag: a running run_once must finish before exit."""
    previous = {}
    try:
        for name in ("SIGINT", "SIGTERM", "SIGBREAK"):
            sig = getattr(signal, name, None)
            if sig is not None:
                previous[sig] = signal.signal(sig, lambda *_: stop.set())
        yield
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)


def stop_on_stdin_eof(stop: threading.Event, stream) -> threading.Thread:
    """Private supervisor pipe; closing it requests cooperative shutdown.

    A single daemon reader also permits graceful owned-child shutdown on Windows
    hosts without a console. No HTTP worker-control endpoint is introduced.
    """
    def watch():
        try:
            while stream.read(1):
                pass
        finally:
            stop.set()
    thread = threading.Thread(target=watch, name="bie-worker-stop", daemon=True)
    thread.start()
    return thread


@dataclass
class WorkerSummary:
    jobs_acked: int = 0
    jobs_failed: int = 0
    idle_polls: int = 0

    def to_safe_dict(self) -> dict[str, int]:
        return {"jobs_acked": self.jobs_acked, "jobs_failed": self.jobs_failed,
                "idle_polls": self.idle_polls}


class PdfInspectionWorkerService:
    """Reuse the existing job transaction/admission/result policy verbatim."""

    def __init__(self, jobs: PdfInspectionJobService, *, poll_interval: float = DEFAULT_POLL_INTERVAL,
                 worker_id: str = "bie-pdf-worker-local"):
        self.poll_interval = validate_poll_interval(poll_interval)
        if not isinstance(worker_id, str) or re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", worker_id) is None:
            raise ValueError("invalid_worker_id")
        self.jobs = jobs
        self.worker_id = worker_id
        self.summary = WorkerSummary()

    def run(self, stop: threading.Event) -> WorkerSummary:
        while not stop.is_set():
            try:
                api_worker_root(self.jobs.data_root)
                # Check again after admission: stop never means cancel the job.
                if stop.is_set():
                    break
                outcome = self.jobs.run_once(self.worker_id).outcome
                if outcome == "IDLE":
                    self.summary.idle_polls += 1
                    stop.wait(self.poll_interval)
                elif outcome == "ACKED":
                    self.summary.jobs_acked += 1
                elif outcome == "FAILED":
                    self.summary.jobs_failed += 1
                else:
                    raise WorkerServiceError("invalid_worker_outcome")
            except Exception:
                raise WorkerServiceError("worker_service_failed") from None
        return self.summary
