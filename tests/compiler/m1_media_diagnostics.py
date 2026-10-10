"""Failure-only child events and owned PID counters; no private output fields.

These observations grant no witness and do not change limits. Anonymous media
events are not executable identities. PID counters are sampled before cleanup,
not atomically with the worker outcome; diagnostic timing overhead is explicit.
"""
from contextlib import contextmanager
import os
from pathlib import Path
import re
import stat
from types import FunctionType, ModuleType

from tests.compiler.m1_safe_paint_diagnostics import (
    UNKNOWN, integer, require, read_receipt, PREFERENCES,
)

MEDIA_SCHEMA = "bie.task036.m1.media-process-observation/1"
PID_SCHEMA = "bie.task036.m1.owned-pid-observation/1"
SIGNALS = frozenset({"SIGABRT", "SIGALRM", "SIGBUS", "SIGFPE", "SIGHUP", "SIGILL", "SIGINT", "SIGKILL",
    "SIGPIPE", "SIGQUIT", "SIGSEGV", "SIGTERM", "SIGTRAP", "SIGXCPU", "SIGXFSZ"})
CODES = frozenset({"EAGAIN", "ENOMEM", "EMFILE", "ENFILE", "EACCES", "ENOENT", "EBADF", "EPIPE",
    "ETIMEDOUT", "ECONNRESET", "ECONNREFUSED"})
STATES = frozenset({"VALID", "ABSENT", "INVALID", "TOO_LARGE", "UNAVAILABLE", UNKNOWN})


def empty_media(state=UNKNOWN):
    return {"schema": MEDIA_SCHEMA, "phase": "RENDER_MEDIA", "receipt_state": state,
        "provenance": "TRUSTED_CAPTURE_CHILD_EVENTS", "manifest_sha256": UNKNOWN,
        "frame_count": UNKNOWN, "spawn_events": UNKNOWN, "events": [],
        "render_passed": False, "accepted": False, "product_accepted": False}


def is_safe_media(value):
    try:
        template = empty_media()
        require(type(value) is dict and set(value) == set(template))
        for key in ("schema", "phase", "provenance"):
            require(type(value[key]) is str and value[key] == template[key])
        require(type(value["receipt_state"]) is str and value["receipt_state"] in STATES)
        require(all(value[k] is False for k in ("render_passed", "accepted", "product_accepted")))
        require(type(value["events"]) is list and len(value["events"]) <= 4)
        if value["receipt_state"] != "VALID":
            require(value["events"] == [] and all(type(value[k]) is str and value[k] == UNKNOWN
                for k in ("manifest_sha256", "frame_count", "spawn_events")))
            return True
        require(type(value["manifest_sha256"]) is str and re.fullmatch(r"[0-9a-f]{64}", value["manifest_sha256"]))
        integer(value["frame_count"], 1, 2400); integer(value["spawn_events"], 0, 128)
        for row in value["events"]:
            require(type(row) is dict and set(row) == {"event", "exit_code", "signal", "error_code"})
            require(type(row["event"]) is str and row["event"] in {"EXIT", "ERROR"})
            require(type(row["signal"]) is str and row["signal"] in SIGNALS | {UNKNOWN})
            require(type(row["error_code"]) is str and row["error_code"] in CODES | {UNKNOWN})
            if type(row["exit_code"]) is not str or row["exit_code"] != UNKNOWN:
                integer(row["exit_code"], -255, 255)
            if row["event"] == "EXIT":
                require(row["error_code"] == UNKNOWN)
            else:
                require(row["exit_code"] == row["signal"] == UNKNOWN)
        return True
    except BaseException:
        return False


def capture_media_observation(owned_root, *, preference, manifest_sha256, frame_count):
    try:
        require(type(preference) is str and preference in PREFERENCES)
        require(type(manifest_sha256) is str and re.fullmatch(r"[0-9a-f]{64}", manifest_sha256))
        integer(frame_count, 1, 2400)
        state, raw = read_receipt(owned_root, owned_root / ("paint-" + preference),
            "MEDIA_PROCESS_DIAGNOSTIC.json", max_bytes=1024)
        if state != "VALID":
            return empty_media(state)
        require(type(raw) is dict and set(raw) == {"schema", "phase", "manifest_sha256", "frame_count",
            "state", "spawn_events", "events", "accepted"})
        require(raw["schema"] == "bie.capture-media-process-failure/1" and raw["phase"] == "RENDER_MEDIA"
            and raw["manifest_sha256"] == manifest_sha256 and raw["frame_count"] == frame_count
            and type(raw["frame_count"]) is int and raw["accepted"] is False)
        if raw["state"] == "UNAVAILABLE":
            require(raw["spawn_events"] == UNKNOWN and raw["events"] == [])
            return empty_media("UNAVAILABLE")
        require(raw["state"] == "VALID")
        result = empty_media("VALID")
        for key in ("manifest_sha256", "frame_count", "spawn_events", "events"):
            result[key] = raw[key]
        require(is_safe_media(result))
        return result
    except BaseException:
        return empty_media("INVALID")


def empty_pids(stage="NOT_CALLED", verified=False):
    return {"schema": PID_SCHEMA, "phase": "BEFORE_OWNED_CGROUP_CLEANUP",
        "provenance": "CANONICAL_OWNED_CGROUP" if verified is True else "UNVERIFIED_TEST_CONTROL",
        "origin_verified": verified is True, "stage": stage, "availability": "UNAVAILABLE",
        "pids_max": UNKNOWN, "max_events": UNKNOWN, "peak_tasks": UNKNOWN,
        "render_passed": False, "accepted": False, "product_accepted": False}


def is_safe_pids(value):
    try:
        template = empty_pids()
        require(type(value) is dict and set(value) == set(template))
        require(value["schema"] == PID_SCHEMA and value["phase"] == template["phase"])
        require(type(value["origin_verified"]) is bool
            and value["provenance"] == empty_pids(verified=value["origin_verified"])["provenance"])
        require(type(value["stage"]) is str and value["stage"] in {"NOT_CALLED", "NONE", "CALL_RAISED",
            "MULTIPLE_CALLS", "BINDING_UNAVAILABLE", "CONTROL_UNAVAILABLE", "OBSERVER_ERROR"})
        require(type(value["availability"]) is str and value["availability"] in {"VALID", "UNAVAILABLE"})
        require(all(value[k] is False for k in ("render_passed", "accepted", "product_accepted")))
        if value["availability"] == "UNAVAILABLE":
            require(all(type(value[k]) is str and value[k] == UNKNOWN for k in ("pids_max", "max_events", "peak_tasks")))
        else:
            require(value["stage"] == "NONE" and type(value["pids_max"]) is int and value["pids_max"] == 128)
            integer(value["max_events"])
            if value["peak_tasks"] != UNKNOWN: integer(value["peak_tasks"])
        return True
    except BaseException:
        return False


def owned_pid_controls(path, inode, base):
    """Only fixed read-only cgroup controls; anchored dir fd on the real Linux host.

    The caller supplies the verified canonical group's path, never a CLI path.
    Separate temporary controls in unit tests prove parsing, not kernel behavior.
    """
    require(type(path) is type(Path()) and type(base) is type(Path()) and path.parent == base
        and path.name.startswith("bie-chromium-owned-") and re.fullmatch(r"bie-chromium-owned-[A-Za-z0-9_-]{1,64}", path.name))
    require(path.is_absolute() and path.resolve(strict=True) == path and not path.is_symlink())
    for parent in (path, *path.parents): require(not parent.is_symlink())
    info = path.lstat()
    require(stat.S_ISDIR(info.st_mode) and type(inode) is int and info.st_ino == inode)
    if hasattr(os, "geteuid"):
        require(info.st_uid == os.geteuid() and not info.st_mode & 0o022)
    dfd = None
    try:
        if os.open in os.supports_dir_fd:
            dfd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            require(os.fstat(dfd).st_ino == inode)
        def read(name):
            before = (path / name).lstat()
            require(stat.S_ISREG(before.st_mode) and not (path / name).is_symlink())
            flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
            fd = os.open(name, flags, dir_fd=dfd) if dfd is not None else os.open(path / name, flags)
            with os.fdopen(fd, "rb") as stream:
                handle = os.fstat(stream.fileno())
                require((handle.st_dev, handle.st_ino) == (before.st_dev, before.st_ino))
                data = stream.read(257)
            require(len(data) <= 256 and (path / name).lstat().st_ino == before.st_ino and path.lstat().st_ino == inode)
            return data
        limit = read("pids.max")
        require(limit.strip() == b"128")
        events = read("pids.events")
        # Only the documented exact max counter is consumed; no arbitrary keys.
        require(re.fullmatch(rb"max [0-9]{1,19}\n?", events))
        count = integer(int(events.split()[1]))
        try:
            peak_raw = read("pids.peak")
        except FileNotFoundError:
            peak = UNKNOWN
        else:
            require(re.fullmatch(rb"[0-9]{1,19}\n?", peak_raw))
            peak = integer(int(peak_raw))
        return count, peak
    finally:
        if dfd is not None: os.close(dfd)


class PidObserver:
    def __init__(self, verified=False):
        self.verified = verified is True
        self.calls = 0
        self.safe = empty_pids(verified=self.verified)

    def delegate(self, original, group, *, base, expected_type):
        # Count invocations, not only returns. A raised original is still a call.
        try: self.calls += 1
        except BaseException: pass
        try:
            returned = original(group)
        except BaseException:
            try: self.safe = empty_pids("MULTIPLE_CALLS" if self.calls != 1 else "CALL_RAISED", self.verified)
            except BaseException: pass
            raise
        try:
            if self.calls != 1:
                self.safe = empty_pids("MULTIPLE_CALLS", self.verified)
            else:
                require(type(group) is expected_type and type(returned) is dict
                    and type(returned.get("pids_max")) is int and returned["pids_max"] == 128)
                count, peak = owned_pid_controls(group.path, group.inode, base)
                self.safe = empty_pids("NONE", self.verified)
                self.safe.update(availability="VALID", pids_max=128, max_events=count, peak_tasks=peak)
        except BaseException:
            try: self.safe = empty_pids("CONTROL_UNAVAILABLE", self.verified)
            except BaseException: pass
        return returned

    def snapshot(self):
        return dict(self.safe) if is_safe_pids(self.safe) else empty_pids("OBSERVER_ERROR", self.verified)


@contextmanager
def observe_owned_pids():
    observer = None
    worker = kind = original = None
    try:
        observer = PidObserver()
        from bie.compiler import chromium_resource_worker as worker
        expected = Path(__file__).resolve().parents[2] / "bie/compiler/chromium_resource_worker.py"
        kind = worker.OwnedMemoryGroup
        original = kind.receipt
        require(type(worker) is ModuleType and type(kind) is type and type(original) is FunctionType
            and Path(worker.__file__).resolve() == expected
            and Path(original.__code__.co_filename).resolve() == expected
            and original.__module__ == "bie.compiler.chromium_resource_worker"
            and original.__name__ == "receipt" and worker.CGROOT == Path("/sys/fs/cgroup"))
        observer.verified = True
        observer.safe = empty_pids(verified=True)
    except BaseException:
        try:
            if observer is not None: observer.safe = empty_pids("BINDING_UNAVAILABLE")
        except BaseException: pass
        yield observer
        return
    def delegate(group):
        return observer.delegate(original, group, base=worker.CGROOT, expected_type=kind)
    try:
        kind.receipt = delegate
    except BaseException:
        try: observer.safe = empty_pids("BINDING_UNAVAILABLE")
        except BaseException: pass
        yield observer
        return
    try:
        yield observer
    finally:
        try: kind.receipt = original
        except BaseException: pass
