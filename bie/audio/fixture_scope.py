"""Explicit local diagnostic scope; synthetic timing never passes by default.

The live neural CLI does not enter this scope. It is for test/fixture execution,
not an acoustic, provider-authenticity or release-acceptance override.
"""
from contextvars import ContextVar
from contextlib import contextmanager

_SYNTHETIC_TIMING = ContextVar('bie_audio_synthetic_timing_diagnostic', default=False)


def synthetic_timing_allowed():
    return _SYNTHETIC_TIMING.get() is True


@contextmanager
def synthetic_timing_scope(*, enabled=True):
    if type(enabled) is not bool:
        raise ValueError('DIAGNOSTIC_SCOPE_BOOLEAN_REQUIRED')
    token = _SYNTHETIC_TIMING.set(enabled)
    try:
        yield
    finally:
        _SYNTHETIC_TIMING.reset(token)
