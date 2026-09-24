"""H8-003: bounded cross-process provider-call admission without a second orchestrator.

Slot locks are OS-released if a process dies. This is host-local admission control,
not a distributed fleet scheduler or autoscaler.
"""
from __future__ import annotations
from contextlib import contextmanager
from pathlib import Path
import fcntl
import os
import stat
import time
from .common import AudioError, fingerprint
from .tts_cache import safe_directory
from .tts_contract import ProviderFailure


class ProviderCallScheduler:
    def __init__(self, root, *, max_inflight=2, admission_timeout_seconds=10.0, sleeper=time.sleep, clock=time.monotonic):
        if type(max_inflight) is not int or not 1 <= max_inflight <= 32:
            raise AudioError('NEURAL_SCHEDULER_INFLIGHT_POLICY')
        if type(admission_timeout_seconds) not in (int, float) or not 0.05 <= admission_timeout_seconds <= 120:
            raise AudioError('NEURAL_SCHEDULER_TIMEOUT_POLICY')
        self.root = safe_directory(root)
        self.max_inflight = max_inflight
        self.admission_timeout_seconds = float(admission_timeout_seconds)
        self._sleep, self._clock = sleeper, clock
        self.slot_paths = tuple(self.root / f'slot-{i:02d}.lock' for i in range(max_inflight))

    @contextmanager
    def acquire(self, call_key: str, *, cancellation=None):
        if type(call_key) is not str or not call_key.startswith('sha256:'):
            raise AudioError('NEURAL_SCHEDULER_CALL_KEY')
        deadline = self._clock() + self.admission_timeout_seconds
        fd = slot = None
        try:
            while fd is None:
                if cancellation is not None and cancellation.is_set():
                    raise ProviderFailure('CANCELLED')
                for index, path in enumerate(self.slot_paths):
                    candidate = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
                    if not stat.S_ISREG(os.fstat(candidate).st_mode):
                        os.close(candidate); raise AudioError('NEURAL_SCHEDULER_SLOT_INVALID')
                    try:
                        fcntl.flock(candidate, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        fd, slot = candidate, index
                        break
                    except BlockingIOError:
                        os.close(candidate)
                if fd is not None:
                    break
                if self._clock() >= deadline:
                    raise ProviderFailure('NEURAL_PROVIDER_CAPACITY_TIMEOUT')
                self._sleep(min(0.05, max(0.0, deadline - self._clock())))
            yield {
                'schema_version': 'bie.audio.provider-slot/1',
                'slot': slot,
                'call_key': call_key,
                'scheduler_fingerprint': fingerprint((str(self.root.name), self.max_inflight, self.admission_timeout_seconds)),
                'distributed_scheduler_verified': False,
                'product_accepted': False,
            }
        finally:
            if fd is not None:
                try: fcntl.flock(fd, fcntl.LOCK_UN)
                finally: os.close(fd)
