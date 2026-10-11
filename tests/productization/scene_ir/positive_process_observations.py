"""Closed test-only child checkpoints, never an execution verdict or payload."""
import json
import os
from pathlib import Path
import stat
import time

SCHEMA = "bie.task036.positive-child-checkpoint/1"
NAME = "scene_ir_positive_checkpoint.json"
MAX_BYTES = 2048
STAGES = ("SOURCE", "DOCUMENT_INTELLIGENCE", "KNOWLEDGE", "PREREQUISITE", "MATH", "REASONING",
    "PEDAGOGY", "DIRECTOR", "VISUAL", "ANIMATION", "SCENE_IR")
PHASES = frozenset({"INITIAL_STATUS", "BEFORE_WORK", "AFTER_WORK", "NATIVE_BOUNDARY", "RETURN"})
BOUNDARIES = frozenset({"UNKNOWN", "after_SCENE_IR_inputs_verified", "after_SCENE_IR_catalog",
    "after_SCENE_IR_adoption", "after_SCENE_IR_validation", "after_SCENE_IR_private_publication",
    "before_SCENE_IR_terminal", "after_SCENE_IR_terminal", "before_next_admission"})
FIELDS = frozenset({"schema", "mode", "phase", "requested_stage", "boundary", "operation_index",
    "process_cpu_ms", "accepted", "product_accepted"})


def validate(row):
    if type(row) is not dict: raise ValueError("CHECKPOINT_SHAPE")
    row = row.copy()  # One builtin snapshot; never re-read the caller after validation.
    if (any(type(key) is not str for key in row) or set(row) != FIELDS
            or type(row["schema"]) is not str or row["schema"] != SCHEMA):
        raise ValueError("CHECKPOINT_SHAPE")
    for key, values in (("mode", ("RUN", "VERIFY")), ("phase", PHASES),
                        ("requested_stage", STAGES + ("UNKNOWN",)), ("boundary", BOUNDARIES)):
        if type(row[key]) is not str or row[key] not in values:
            raise ValueError("CHECKPOINT_ENUM")
    if type(row["operation_index"]) is not int or not 0 <= row["operation_index"] <= 11:
        raise ValueError("CHECKPOINT_INDEX")
    cpu = row["process_cpu_ms"]
    if cpu is not None and (type(cpu) is not int or not 0 <= cpu <= 60000):
        raise ValueError("CHECKPOINT_CPU")
    if row["accepted"] is not False or row["product_accepted"] is not False:
        raise ValueError("CHECKPOINT_ACCEPTANCE")
    return {key: row[key] for key in sorted(FIELDS)}


def write(root, row):
    """Atomic bounded replacement in the owned fixture root; errors contained."""
    try:
        root = Path(root)
        target, temporary = root / NAME, root / (NAME + ".new")
        if root.is_symlink() or not root.is_dir() or target.is_symlink() or temporary.is_symlink():
            return False
        if target.exists() and not stat.S_ISREG(target.lstat().st_mode): return False
        raw = json.dumps(validate(row), sort_keys=True).encode("utf-8")
        if len(raw) > MAX_BYTES: return False
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        with os.fdopen(os.open(temporary, flags, 0o600), "wb") as stream:
            stream.write(raw)
        os.replace(temporary, target)
        return True
    except BaseException:
        return False
    # An interrupted optional write remains private for the existing fixture
    # TemporaryDirectory cleanup; no pre-existing file is removed here.


def read(root):
    try:
        root = Path(root)
        if root.is_symlink() or not root.is_dir(): return "INVALID", None
        target = root / NAME
        before = target.lstat()
        if target.is_symlink() or not stat.S_ISREG(before.st_mode): return "INVALID", None
        if before.st_size > MAX_BYTES: return "TOO_LARGE", None
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        with os.fdopen(os.open(target, flags), "rb") as stream:
            opened = os.fstat(stream.fileno())
            identity = lambda s: (s.st_ino, s.st_size, s.st_mtime_ns)
            if not stat.S_ISREG(opened.st_mode) or identity(opened) != identity(before): return "INVALID", None
            raw = stream.read(MAX_BYTES + 1)
        after = target.lstat()
        if identity(before) != identity(after) or len(raw) != before.st_size: return "INVALID", None
        def pairs(items):
            value = {}
            for key, child in items:
                if key in value: raise ValueError("DUPLICATE")
                value[key] = child
            return value
        def nonfinite(_): raise ValueError("NONFINITE")
        row = validate(json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite))
        return "VALID", row
    except FileNotFoundError:
        return "ABSENT", None
    except BaseException:
        return "INVALID", None


class Checkpoints:
    """Optional observations around the real calls; no caching or selection."""
    def __init__(self, root, mode):
        if type(mode) is not str or mode not in ("RUN", "VERIFY"): raise ValueError("CHECKPOINT_MODE")
        self.root, self.mode = root, mode
        self.stage, self.index = "UNKNOWN", 0

    def mark(self, phase, stage="UNKNOWN", index=0, boundary="UNKNOWN"):
        try:
            cpu = round(time.process_time() * 1000)
            row = validate(dict(schema=SCHEMA, mode=self.mode, phase=phase, requested_stage=stage,
                operation_index=index, boundary=boundary, process_cpu_ms=cpu,
                accepted=False, product_accepted=False))
            self.stage, self.index = stage, index
            write(self.root, row)
        except BaseException:
            pass  # Never replace the real status/worker/cleanup outcome.

    def fault(self, boundary):
        if type(boundary) is str and boundary in BOUNDARIES and boundary != "UNKNOWN":
            self.mark("NATIVE_BOUNDARY", self.stage, self.index, boundary)
