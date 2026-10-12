"""Test-only original exception sites; no exception values or private frames.

This current-thread observer does not establish an inner process outcome or final
cause. Tracing has nonzero scheduling overhead. An existing tracer is never
replaced. Canonical rendering, arguments, receipts and cleanup remain unchanged.
"""
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
import sys
from types import CodeType, FrameType, FunctionType, ModuleType

SCHEMA = "bie.task036.m1.parent-exception-site-observation/1"
SOURCE_SHA256 = "aeedfc527fb47df33c448ad2bf1a2553574015e3124a14e35fae1e94f75c2963"
UNKNOWN = "UNKNOWN"
MAX_EVENTS = 32
REASONS = frozenset({"NONE", "SOURCE_UNAVAILABLE", "EXISTING_TRACER", "SETUP_FAILED",
    "CALLBACK_FAILED", "RESTORATION_CHANGED", "RESTORATION_FAILED"})
SITES = frozenset({"MONITOR_COMMAND_READ", "MONITOR_EXE_OR_ROOT_LINK", "MONITOR_LIMIT_READ",
    "MONITOR_MAPS_READ", "DRIVER_COMMUNICATE", "DRIVER_RESULT_READ", "POST_RUN_ENGINE_HASH",
    "POST_RUN_BROWSER_HASH", "CLEANUP_GROUP", "CLEANUP_DRIVER", "CLEANUP_TEMPORARY",
    "RESOURCE_RECEIPT_PUBLICATION", "RUN_OTHER", "GRANT_OTHER", "BOUNDED_READ_OPEN_OR_READ", "BOUNDED_READ_OTHER", "FILE_HASH_OPEN",
    "FILE_HASH_READ", "FILE_HASH_OTHER"})
LOCATIONS = {
    "run_chromium_isolated": {347: "MONITOR_COMMAND_READ", 360: "MONITOR_EXE_OR_ROOT_LINK",
        362: "MONITOR_LIMIT_READ", 363: "MONITOR_MAPS_READ", 372: "DRIVER_COMMUNICATE",
        375: "DRIVER_RESULT_READ", 388: "POST_RUN_ENGINE_HASH", 389: "POST_RUN_BROWSER_HASH",
        398: "CLEANUP_GROUP", 405: "CLEANUP_DRIVER", 407: "CLEANUP_TEMPORARY",
        412: "RESOURCE_RECEIPT_PUBLICATION"},
    "_grant": {}, "bounded_read": {76: "BOUNDED_READ_OPEN_OR_READ"},
    "file_sha": {71: "FILE_HASH_OPEN", 72: "FILE_HASH_READ"},
}
DEFAULTS = {"run_chromium_isolated": "RUN_OTHER", "_grant": "GRANT_OTHER",
    "bounded_read": "BOUNDED_READ_OTHER", "file_sha": "FILE_HASH_OTHER"}


def empty_observation(reason="SOURCE_UNAVAILABLE"):
    return dict(schema=SCHEMA, provenance="SOURCE_PINNED_CURRENT_THREAD_EXCEPTION_EVENTS",
        source_sha256=SOURCE_SHA256, scope="OBSERVED_EVENTS_NOT_FINAL_CAUSE_OR_PROCESS_VERDICT",
        exception_kind="PERMISSION_ERROR", binding_verified=False, availability="UNAVAILABLE",
        reason=reason if reason in REASONS else "SOURCE_UNAVAILABLE", trace_installed=False,
        binding_restored=UNKNOWN, selected_exception_events=UNKNOWN, first_site=UNKNOWN,
        last_site=UNKNOWN, event_limit_reached=UNKNOWN, render_passed=False, accepted=False,
        product_accepted=False)


def is_safe_observation(value):
    try:
        template = empty_observation()
        if type(value) is not dict or set(value) != set(template): return False
        if any(type(k) is not str for k in value): return False
        for name in ("schema", "provenance", "source_sha256", "scope", "exception_kind"):
            if type(value[name]) is not str or value[name] != template[name]: return False
        for name in ("binding_verified", "trace_installed"):
            if type(value[name]) is not bool: return False
        if not (type(value["binding_restored"]) is bool or
                (type(value["binding_restored"]) is str and value["binding_restored"] == UNKNOWN)): return False
        if type(value["availability"]) is not str or value["availability"] not in {"VALID", "UNAVAILABLE", "INVALID"}: return False
        if type(value["reason"]) is not str or value["reason"] not in REASONS: return False
        for name in ("first_site", "last_site"):
            if type(value[name]) is not str or value[name] not in SITES | {UNKNOWN}: return False
        for name in ("render_passed", "accepted", "product_accepted"):
            if value[name] is not False: return False
        if value["availability"] == "VALID":
            n = value["selected_exception_events"]
            if type(n) is not int or not 0 <= n <= MAX_EVENTS: return False
            if type(value["event_limit_reached"]) is not bool: return False
            if not value["binding_verified"] or not value["trace_installed"] or value["reason"] != "NONE": return False
            if value["binding_restored"] is False: return False
            if n == 0 and (value["first_site"] != UNKNOWN or value["last_site"] != UNKNOWN): return False
            if n > 0 and (value["first_site"] == UNKNOWN or value["last_site"] == UNKNOWN): return False
            if value["event_limit_reached"] and n != MAX_EVENTS: return False
        else:
            if value["reason"] == "NONE": return False
            if any(type(value[k]) is not str or value[k] != UNKNOWN for k in
                    ("selected_exception_events", "first_site", "last_site", "event_limit_reached")): return False
        return True
    except BaseException:
        return False


def canonical_targets():
    from bie.compiler import chromium_resource_worker as worker
    path = Path(__file__).resolve().parents[2] / "bie/compiler/chromium_resource_worker.py"
    if type(worker) is not ModuleType or Path(worker.__file__).resolve() != path.resolve(): raise ValueError("SOURCE_BINDING")
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 65536: raise ValueError("SOURCE_BINDING")
    with path.open("rb") as stream:
        source = stream.read(65537)
    if len(source) > 65536: raise ValueError("SOURCE_BINDING")
    if sha256(source).hexdigest() != SOURCE_SHA256: raise ValueError("SOURCE_BINDING")
    # Compile public pinned source without executing it. Reject forged/replaced
    # functions even when their filename/module string looks canonical.
    expected = {c.co_name: c for c in compile(source, str(path.resolve()), "exec", dont_inherit=True).co_consts
                if type(c) is CodeType and c.co_name in LOCATIONS}
    targets = []
    for name in LOCATIONS:
        function = getattr(worker, name)
        if (type(function) is not FunctionType or function.__module__ != worker.__name__
                or function.__name__ != name or function.__code__ != expected.get(name)
                or function.__globals__ is not worker.__dict__):
            raise ValueError("SOURCE_BINDING")
        targets.append((function.__code__, name))
    return tuple(targets)


class ExceptionSiteObserver:
    def __init__(self, targets=()):
        self._targets = targets
        self._safe = empty_observation()
        if targets:
            self._safe.update(binding_verified=True, availability="VALID", reason="NONE",
                selected_exception_events=0, event_limit_reached=False)

    def unavailable(self, reason):
        previous = self._safe
        self._safe = empty_observation(reason)
        for name in ("binding_verified", "trace_installed", "binding_restored"):
            self._safe[name] = previous[name]
        if reason in {"CALLBACK_FAILED", "RESTORATION_CHANGED", "RESTORATION_FAILED"}:
            self._safe["availability"] = "INVALID"

    def trace(self, frame, event, arg):
        try:
            if type(frame) is not FrameType: return None
            name = next((name for code, name in self._targets if frame.f_code is code), None)
            if name is None: return None
            # No locals/globals/arguments/exception value/traceback access.
            frame.f_trace_lines = False
            frame.f_trace_opcodes = False
            if self._safe["availability"] != "VALID": return None
            if event == "exception" and type(arg) is tuple and len(arg) == 3 and arg[0] is PermissionError:
                n = self._safe["selected_exception_events"]
                if n >= MAX_EVENTS:
                    self._safe["event_limit_reached"] = True
                    return None
                line = frame.f_lineno
                site = LOCATIONS[name].get(line, DEFAULTS[name])
                self._safe["selected_exception_events"] = n + 1
                if n == 0: self._safe["first_site"] = site
                self._safe["last_site"] = site
            return self.trace
        except BaseException:
            try: self.unavailable("CALLBACK_FAILED")
            except BaseException: pass
            return None

    def snapshot(self):
        try:
            safe = dict(self._safe)
            return safe if is_safe_observation(safe) else empty_observation("CALLBACK_FAILED")
        except BaseException:
            return empty_observation("CALLBACK_FAILED")


@contextmanager
def observe_parent_exception_sites():
    observer = None
    installed = False
    callback = None
    try:
        observer = ExceptionSiteObserver()
        if sys.gettrace() is not None:
            observer.unavailable("EXISTING_TRACER")
        else:
            observer = ExceptionSiteObserver(canonical_targets())
            callback = observer.trace
            try:
                sys.settrace(callback)
                installed = True
                observer._safe["trace_installed"] = True
            except BaseException:
                observer.unavailable("SETUP_FAILED")
                # Contain an unusual partial-install failure without leaving our
                # tracer active. Never replace a distinct tracer on this path.
                try:
                    installed = sys.gettrace() is callback
                    observer._safe["trace_installed"] = installed
                except BaseException:
                    pass
    except BaseException:
        try:
            if observer is not None: observer.unavailable("SOURCE_UNAVAILABLE")
        except BaseException:
            pass
    try:
        yield observer
    finally:
        # Check our exact callback even following partial setup. Native call
        # return/rejection must survive any optional bookkeeping fault.
        if callback is not None:
            restored, reason = UNKNOWN, None
            try:
                if sys.gettrace() is callback:
                    sys.settrace(None)
                    restored = True
                elif installed:
                    # Do not overwrite a tracer installed by the delegate.
                    restored, reason = False, "RESTORATION_CHANGED"
            except BaseException:
                restored, reason = False, "RESTORATION_FAILED"
            try:
                observer._safe["binding_restored"] = restored
                if reason is not None: observer.unavailable(reason)
            except BaseException:
                pass
