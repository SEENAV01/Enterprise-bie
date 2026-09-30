"""Hard-deadline wrapper for a trusted provider factory (not a hostile-code sandbox).

Factory and adapter are operator-installed Python code, never candidate input.
spawn uses Python serialization for that trusted factory. Responses cross a bounded
UTF-8 file channel, never pickle. A timeout kills/reaps the direct worker. OS-level
network, memory and descendant-process containment remain deployment responsibilities.
No live provider is configured here. Factories should return adapters owning finite
network timeouts too. Call from a normal guarded Python entry point on Windows.
"""
from __future__ import annotations
from contextlib import redirect_stdout, redirect_stderr
import math
import multiprocessing as mp
import os
from pathlib import Path
import tempfile
import time
from ..models import BenchmarkError, canonical_json, strict_loads, ident


def _worker(factory, request_raw, identity, directory, limit):
    # Suppress provider prints/tracebacks that may contain credentials.
    with open(os.devnull, 'w') as quiet, redirect_stdout(quiet), redirect_stderr(quiet):
        try:
            provider = factory()
            actual = (provider.provider_id, provider.model_version, provider.fixture_only)
            if (actual != identity or type(provider.fixture_only) is not bool):
                raise BenchmarkError('SUPERVISED_PROVIDER_IDENTITY_MISMATCH')
            raw = provider.complete(strict_loads(request_raw))
            if (provider.provider_id, provider.model_version, provider.fixture_only) != identity or type(provider.fixture_only) is not bool:
                raise BenchmarkError('MODEL_PROVIDER_CHANGED_DURING_CALL')
            if type(raw) is not str or len(raw.encode('utf-8')) > limit:
                raise BenchmarkError('MODEL_RESPONSE_SIZE_LIMIT')
            envelope = {'status': 'OK', 'response': raw}
        except BenchmarkError as exc:
            envelope = {'status': 'BLOCKED', 'reason': exc.code}
        except BaseException:
            envelope = {'status': 'BLOCKED', 'reason': 'SUPERVISED_PROVIDER_FAILURE'}
        try:
            raw = canonical_json(envelope).encode('utf-8')
            stage = Path(directory)/'response.tmp'
            with stage.open('xb') as f:
                f.write(raw)
                f.flush()
                os.fsync(f.fileno())
            os.replace(stage, Path(directory)/'response.json')
        except BaseException:
            # Parent reports a missing/invalid result as BLOCKED.
            return


class SupervisedProvider:
    def __init__(self, factory, *, provider_id, model_version, fixture_only,
                 timeout_seconds=30.0, response_limit=128000):
        if not callable(factory):
            raise BenchmarkError('INVALID_PROVIDER_FACTORY')
        ident(provider_id); ident(model_version)
        if type(fixture_only) is not bool:
            raise BenchmarkError('INVALID_PROVIDER_FIXTURE_FLAG')
        if type(timeout_seconds) not in (int, float) or not math.isfinite(timeout_seconds) or not 0.05 <= timeout_seconds <= 300:
            raise BenchmarkError('INVALID_PROVIDER_DEADLINE')
        if type(response_limit) is not int or not 128 <= response_limit <= 128000:
            raise BenchmarkError('INVALID_PROVIDER_RESPONSE_LIMIT')
        self.factory = factory
        self.provider_id, self.model_version, self.fixture_only = provider_id, model_version, fixture_only
        self.timeout_seconds, self.response_limit = timeout_seconds, response_limit
        self.last_observation = None

    def complete(self, request):
        request_raw = canonical_json(request)
        if len(request_raw.encode()) > 256000:
            raise BenchmarkError('MODEL_REQUEST_SIZE_LIMIT')
        identity = (self.provider_id, self.model_version, self.fixture_only)
        started = time.monotonic()
        proc = None
        timed_out = False
        with tempfile.TemporaryDirectory(prefix='bie-evaluator-') as directory:
            try:
                proc = mp.get_context('spawn').Process(
                    target=_worker, args=(self.factory, request_raw, identity, directory, self.response_limit), daemon=True)
                proc.start()
                proc.join(max(0, self.timeout_seconds - (time.monotonic()-started)))
                if proc.is_alive():
                    timed_out = True
                    raise BenchmarkError('MODEL_PROVIDER_DEADLINE_EXCEEDED')
                if proc.exitcode != 0:
                    raise BenchmarkError('SUPERVISED_PROVIDER_EXIT_FAILED')
                path = Path(directory)/'response.json'
                if path.is_symlink() or not path.is_file() or path.stat().st_size > 1_000_000:
                    raise BenchmarkError('SUPERVISED_PROVIDER_RESULT_MISSING')
                with path.open('rb') as f:
                    data = strict_loads(f.read(1_000_001))
                if type(data) is not dict:
                    raise BenchmarkError('SUPERVISED_PROVIDER_PROTOCOL')
                if data.get('status') == 'BLOCKED' and set(data) == {'status', 'reason'}:
                    raise BenchmarkError(ident(data['reason']))
                if set(data) != {'status', 'response'} or data['status'] != 'OK' or type(data['response']) is not str:
                    raise BenchmarkError('SUPERVISED_PROVIDER_PROTOCOL')
                if len(data['response'].encode()) > self.response_limit:
                    raise BenchmarkError('MODEL_RESPONSE_SIZE_LIMIT')
                return data['response']
            except BenchmarkError:
                raise
            except Exception:
                raise BenchmarkError('SUPERVISED_PROVIDER_START_OR_IO_FAILED') from None
            finally:
                if proc is not None and proc.pid is not None:
                    if proc.is_alive():
                        proc.terminate(); proc.join(0.25)
                    if proc.is_alive():
                        proc.kill(); proc.join(0.25)
                    alive = proc.is_alive()
                    self.last_observation = {'deadline_exceeded': timed_out, 'worker_reaped': not alive,
                        'worker_exitcode': proc.exitcode, 'elapsed_seconds': time.monotonic()-started,
                        'live_provider_verified': False, 'os_sandbox_verified': False}
                    if not alive:
                        proc.close()
