"""Test-only closed recovery-child evidence; no private output is inspected."""
from contextlib import contextmanager
from contextvars import ContextVar
import json
import os
from math import isfinite
from pathlib import Path
import stat

from apps.operator.process_supervision import ChildOutcome

SCHEMA = 'bie.task036.recovery-child-observation/1'
LEGACY_CHILD_SCHEMA = 'bie.task036.recovery-child-guard/1'
CHILD_SCHEMA = 'bie.task036.recovery-child-guard/2'
NAME = 'scene_ir_recovery_probe.json'
POSIX_SIGNALS = os.name == 'posix'
PHASES = frozenset({'START', 'ENFORCE', 'WORK', 'RECOVERY'})
BOUNDARIES = frozenset({'UNKNOWN', 'after_SCENE_IR_inputs_verified', 'after_SCENE_IR_catalog',
    'after_SCENE_IR_adoption', 'after_SCENE_IR_validation', 'after_SCENE_IR_private_publication',
    'after_SCENE_IR_terminal'})
REQUESTED = frozenset({'after_SCENE_IR_private_publication', 'after_SCENE_IR_terminal'})
LEGACY_CODES = frozenset({'CHILD_EXIT_BOUNDARY_REACHED', 'CHILD_STAGE_RETURNED', 'CHILD_EXCEPTION',
    'CHILD_RECOVERED', 'CHILD_RECOVERY_INCOMPLETE'})
CODES = LEGACY_CODES | frozenset({'CHILD_OPERATION_STARTED'})
CLASSES = frozenset({'NONE', 'UNKNOWN', 'ProducerError', 'OperatorError', 'CompilerQAError',
    'ElementCompilerError', 'ValueError', 'RuntimeError', 'MemoryError', 'ModuleNotFoundError',
    'PermissionError', 'OSError', 'FileNotFoundError'})
STATES = frozenset({'UNKNOWN', 'SUCCEEDED', 'FAILED', 'BLOCKED', 'PENDING', 'READY', 'RUNNING'})
FIELDS = frozenset({'schema', 'mode', 'phase', 'last_boundary', 'code', 'exception_class', 'scene_ir_state',
    'accepted', 'product_accepted'})
_ROWS = ContextVar('task036_safe_recovery_test_observations', default=None)


def child_guard(phase, boundary, code, exception_class='NONE', state='UNKNOWN', mode='CRASH'):
    for value, allowed in ((phase, PHASES), (boundary, BOUNDARIES), (code, CODES),
                           (exception_class, CLASSES), (state, STATES), (mode, ('CRASH', 'RECOVER'))):
        if type(value) is not str or value not in allowed:
            raise ValueError('SAFE_CHILD_ENUM')
    return dict(schema=CHILD_SCHEMA, mode=mode, phase=phase, last_boundary=boundary, code=code,
        exception_class=exception_class, scene_ir_state=state, accepted=False, product_accepted=False)


def validate_guard(row):
    if type(row) is not dict or set(row) != FIELDS or type(row['schema']) is not str or row['schema'] not in (CHILD_SCHEMA, LEGACY_CHILD_SCHEMA) or row['accepted'] is not False or row['product_accepted'] is not False:
        raise ValueError('SAFE_CHILD_SHAPE')
    for key in ('mode', 'phase', 'last_boundary', 'code', 'exception_class', 'scene_ir_state'):
        if type(row[key]) is not str:
            raise ValueError('SAFE_CHILD_TYPE')
    if row['schema'] == LEGACY_CHILD_SCHEMA and row['code'] not in LEGACY_CODES:
        raise ValueError('SAFE_CHILD_VERSION')
    result = child_guard(row['phase'], row['last_boundary'], row['code'], row['exception_class'], row['scene_ir_state'], row['mode'])
    result['schema'] = row['schema']  # Never relabel historical guard bytes.
    return result


def write_guard(root, row):
    """A failed evidence write cannot replace a crash/exception/return outcome."""
    try:
        root = Path(root)
        target = root / NAME
        if not root.is_dir() or root.is_symlink() or target.is_symlink():
            return False
        raw = json.dumps(validate_guard(row), sort_keys=True)
        if len(raw.encode()) > 2048:
            return False
        # Never follow an existing file. Replacing a prior safe, regular guard is
        # allowed only in this test-owned directory; absence is not a PASS.
        if target.exists():
            if not stat.S_ISREG(target.lstat().st_mode): return False
            target.unlink()
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
        with os.fdopen(os.open(target, flags, 0o600), 'w', encoding='utf-8') as stream:
            stream.write(raw)
        return True
    except Exception:
        return False


def read_guard(root):
    target = Path(root) / NAME
    try:
        if Path(root).is_symlink() or not Path(root).is_dir():
            return 'INVALID', None
        before = target.lstat()
        if not stat.S_ISREG(before.st_mode) or target.is_symlink() or before.st_size > 2048:
            return 'INVALID', None
        flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
        with os.fdopen(os.open(target, flags), 'rb') as stream:
            opened = os.fstat(stream.fileno())
            if not stat.S_ISREG(opened.st_mode) or (opened.st_ino, opened.st_size, opened.st_mtime_ns) != (before.st_ino, before.st_size, before.st_mtime_ns):
                return 'INVALID', None
            raw = stream.read(2049)
        after = target.lstat()
        if len(raw) > 2048 or len(raw) != before.st_size or (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
            return 'INVALID', None
        def pairs(items):
            result = {}
            for key, value in items:
                if key in result: raise ValueError('DUPLICATE')
                result[key] = value
            return result
        def nonfinite(_): raise ValueError('NONFINITE')
        value = json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)
        return 'VALID', validate_guard(value)
    except FileNotFoundError:
        return 'ABSENT', None
    except Exception:
        return 'INVALID', None


def observe(outcome, root, requested, mode, elapsed):
    """Only typed bounded scalars and our separate closed guard, never output."""
    if type(outcome) is not ChildOutcome or type(requested) is not str or requested not in REQUESTED or type(mode) is not str or mode not in ('CRASH', 'RECOVER'):
        raise ValueError('SAFE_OBSERVATION_INPUT')
    code = outcome.exit_code if type(outcome.exit_code) is int and -255 <= outcome.exit_code <= 255 else None
    duration = round(elapsed, 3) if type(elapsed) in (int, float) and isfinite(elapsed) and 0 <= elapsed <= 60 else None
    state, guard = read_guard(root)
    if guard is not None and guard['mode'] != mode:
        state, guard = 'INVALID', None  # A prior crash is not recovery evidence.
    row = dict(schema=SCHEMA, mode=mode, requested_boundary=requested,
        completed=outcome.completed if type(outcome.completed) is bool else None, exit_code=code,
        signal_number=-code if POSIX_SIGNALS and code is not None and -64 <= code < -1 else None,
        child_wall_seconds=duration, configured_wall_seconds=45, configured_cpu_seconds=30,
        guard_state=state, guard=guard, accepted=False, product_accepted=False)
    rows = _ROWS.get()
    if rows is not None and len(rows) < 4:
        rows.append(row)
    return row


def record_observation(*args):
    """Optional evidence must never mask the original supervision assertions."""
    try:
        return observe(*args)
    except Exception:
        return None


@contextmanager
def capture_observations():
    rows = []
    marker = _ROWS.set(rows)
    try:
        yield rows
    finally:
        _ROWS.reset(marker)
