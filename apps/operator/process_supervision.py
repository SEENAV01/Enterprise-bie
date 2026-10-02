"""Bounded parent supervision for trusted local PDF child entry points.

No shell, request-controlled code, network sandbox claim or implicit retry.
The independent parent enforces wall time even if the child holds Python's GIL.
"""
from dataclasses import dataclass
import os
import subprocess
import threading


@dataclass(frozen=True)
class ChildOutcome:
    exit_code: int
    output: bytes
    completed: bool


def child_environment():
    allowed = ('SystemRoot', 'WINDIR', 'TEMP', 'TMP', 'TMPDIR', 'LANG', 'LC_ALL', 'LD_LIBRARY_PATH')
    result = {key: value for key, value in os.environ.items() if key in allowed}
    result.update(PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
    return result


def supervise(command, env, budget, data=None):
    """All callers are trusted code. Output ceiling is fixed at 4096 bytes."""
    try:
        child = subprocess.Popen(command, stdin=subprocess.PIPE if data is not None else subprocess.DEVNULL,
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env,
                                 creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    except OSError:
        return ChildOutcome(-1, b'', False)
    output = bytearray()
    overflow = threading.Event()

    def kill():
        try:child.kill()
        except ProcessLookupError:pass

    def read():
        try:
            while True:
                chunk = child.stdout.read(1024)
                if not chunk:return
                if len(output) + len(chunk) > 4096:
                    overflow.set();kill();return
                output.extend(chunk)
        except OSError:overflow.set();kill()

    def write():
        try:
            child.stdin.write(data)
            child.stdin.close()
        except (BrokenPipeError, OSError):pass

    reader = threading.Thread(target=read, daemon=True)
    writer = threading.Thread(target=write, daemon=True) if data is not None else None
    reader.start()
    if writer:writer.start()
    timed_out = False
    try:
        try:child.wait(timeout=budget.wall_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True;kill();child.wait(timeout=5)
        if writer:writer.join(timeout=5)
        reader.join(timeout=5)
        complete = not timed_out and not overflow.is_set() and not reader.is_alive() and (writer is None or not writer.is_alive())
        return ChildOutcome(child.returncode, bytes(output), complete)
    finally:
        if child.poll() is None:kill();child.wait(timeout=5)
        if writer:writer.join(timeout=5);child.stdin.close()
        reader.join(timeout=5);child.stdout.close()
