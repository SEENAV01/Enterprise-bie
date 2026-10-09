"""Bounded test-only evidence, never a painter verdict or private receipt export.

Inputs are the two fixed files in this wrapper's owned paint directory. The
private documents contain commands, stderr and paths: none are copied to output.
Missing observations remain UNKNOWN, not zero/false. No native engine is called.
"""
import json
import os
from pathlib import Path
import stat

SCHEMA = "bie.task036.m1.paint-process-diagnostic/1"
UNKNOWN = "UNKNOWN"
FAMILIES = frozenset({"quantitative", "chronology", "cellular", "cellular_reduced"})
PREFERENCES = frozenset({"standard", "reduced"})
STATES = frozenset({"VALID", "ABSENT", "INVALID", "TOO_LARGE", UNKNOWN})
OUTCOMES = frozenset({"SUCCEEDED", "FAILED", "TIMED_OUT", "CANCELLED", "OUTPUT_LIMIT", "SPAWN_ERROR"})
# Parsing bounds only; these do not change any worker/process/resource budget.
MAX_INPUT_BYTES = 256 * 1024
MAX_NODES = 8192
MAX_COUNTER = 2**63 - 1
MAX_DURATION_MS = 3_700_000
EVENTS = ("oom", "oom_kill", "high", "max")
FAILURE_CODES = {
    "CHROMIUM_RESOURCE_HOST_DEADLINE": "HOST_DEADLINE",
    "CHROMIUM_RESOURCE_DRIVER_RESULT": "DRIVER_RESULT",
    "CHROMIUM_RESOURCE_DRIVER_EXIT": "DRIVER_EXIT",
    "CHROMIUM_RESOURCE_DRIVER_FAILED": "DRIVER_FAILED",
    "CHROMIUM_RESOURCE_KERNEL_POLICY": "KERNEL_POLICY",
    "CHROMIUM_RESOURCE_NO_BROWSER_ADMISSION": "NO_BROWSER_ADMISSION",
    "CHROMIUM_RESOURCE_PROCESS_BOUND": "PROCESS_BOUND",
    "CHROMIUM_RESOURCE_CHROME_LIMIT": "CHROME_LIMIT",
    "CHROMIUM_RESOURCE_FULL_RESERVATION_NOT_OBSERVED": "FULL_RESERVATION_NOT_OBSERVED",
    "MEMORY_EXHAUSTED": "MEMORY_EXHAUSTED",
    "CLEANUP_FAILED": "CLEANUP_FAILED",
    "CANCELLED": "CANCELLED",
}
RESOURCE_FIELDS = frozenset({"schema", "node_address_space_bytes", "chromium_address_space_bytes",
    "physical_memory_bytes", "swap_max", "command", "kind", "grants", "security_policy_weakened",
    "accepted", "driver_stderr", "driver_failure", "kernel", "trusted_engine_rows",
    "browser_bytes_unchanged", "entry_mapping_diagnostic", "memory_cgroup", "browser_mappings",
    "owned_cgroup_removed", "cleanup_failure", "owned_processes_reaped", "failure", "process_passed"})


def require(condition):
    if not condition:
        raise ValueError("M1_DIAGNOSTIC_INVALID")


def integer(value, low=0, high=MAX_COUNTER):
    require(type(value) is int and low <= value <= high)
    return value


def boolean(value):
    require(type(value) is bool)
    return value


def pairs(items):
    result = {}
    for key, value in items:
        require(key not in result)
        result[key] = value
    return result


def strict_json(data):
    def nonfinite(_):
        raise ValueError("M1_DIAGNOSTIC_INVALID")
    value = json.loads(data.decode("utf-8"), object_pairs_hook=pairs, parse_constant=nonfinite)
    nodes = 0

    def bounded(item, depth):
        nonlocal nodes
        nodes += 1
        require(nodes <= MAX_NODES and depth <= 20)
        if type(item) is dict:
            require(len(item) <= 256)
            for key, child in item.items():
                require(type(key) is str and len(key) <= 256)
                bounded(child, depth + 1)
        elif type(item) is list:
            require(len(item) <= 2048)
            for child in item:
                bounded(child, depth + 1)
        elif type(item) is str:
            require(len(item) <= MAX_INPUT_BYTES)
        elif type(item) is float:
            import math
            require(math.isfinite(item))
        else:
            require(item is None or type(item) in (bool, int))
            if type(item) is int:
                require(-MAX_COUNTER <= item <= MAX_COUNTER)
    bounded(value, 0)
    require(type(value) is dict)
    return value


def signature(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink, info.st_size,
            info.st_mtime_ns, info.st_ctime_ns)


def file_identity(info):
    # Compare identity/bytes across pathname and handle APIs. Windows can
    # report creation vs change time differently in their st_ctime fields;
    # full timestamp stability is checked separately within EACH API below.
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink, info.st_size, info.st_mtime_ns)


def directory(path):
    require(path.is_absolute())
    for parent in (path, *path.parents):
        info = parent.lstat()
        require(stat.S_ISDIR(info.st_mode) and not parent.is_symlink()
                and not getattr(parent, "is_junction", lambda: False)())
    require(path.resolve(strict=True) == path)
    return signature(path.lstat())


def read_receipt(root, output, name):
    """No traversal or link following; Linux opens against an anchored dir fd."""
    try:
        root_before = directory(root)
        try:
            output.lstat()
        except FileNotFoundError:
            return "ABSENT", None
        output_before = directory(output)
        path = output / name
        before = path.lstat()
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and not path.is_symlink())
        if before.st_size > MAX_INPUT_BYTES:
            return "TOO_LARGE", None
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        dfd = None
        try:
            if os.open in os.supports_dir_fd:
                dfd = os.open(output, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
                require(signature(os.fstat(dfd)) == output_before)
                fd = os.open(name, flags, dir_fd=dfd)
            else:
                fd = os.open(path, flags)
            with os.fdopen(fd, "rb") as stream:
                handle_before = os.fstat(stream.fileno())
                require(file_identity(handle_before) == file_identity(before))
                data = stream.read(MAX_INPUT_BYTES + 1)
                require(signature(os.fstat(stream.fileno())) == signature(handle_before))
            require(signature(path.lstat()) == signature(before)
                    and directory(root) == root_before and directory(output) == output_before)
        finally:
            if dfd is not None:
                os.close(dfd)
        if len(data) > MAX_INPUT_BYTES:
            return "TOO_LARGE", None
        require(len(data) == before.st_size)
        return "VALID", strict_json(data)
    except FileNotFoundError:
        return "ABSENT", None
    except (ValueError, UnicodeError, RecursionError):
        return "INVALID", None
    except OSError:
        return UNKNOWN, None


def empty(family, preference, frame_count=UNKNOWN, timeout=UNKNOWN):
    return {"schema": SCHEMA, "phase": "REAL_GENERATED_CONSUMER",
        "family": family, "preference": preference, "planned_frame_count": frame_count,
        "configured_timeout_s": timeout,
        "process": {"receipt_state": UNKNOWN, "outcome": UNKNOWN, "started": UNKNOWN,
            "process_passed": UNKNOWN, "exit_code": UNKNOWN, "signal_number": UNKNOWN,
            "duration_ms": UNKNOWN, "kernel_enforced": UNKNOWN},
        "resource": {"receipt_state": UNKNOWN, "process_passed": UNKNOWN,
            "kernel_enforced": UNKNOWN, "security_policy_weakened": UNKNOWN,
            "owned_processes_reaped": UNKNOWN, "owned_cgroup_removed": UNKNOWN,
            "failure_code": UNKNOWN, "memory_events": {key: UNKNOWN for key in EVENTS},
            "memory_peak_bytes": UNKNOWN, "physical_memory_bytes": UNKNOWN,
            "swap_max_bytes": UNKNOWN, "pids_max": UNKNOWN},
        "render_passed": False, "accepted": False, "product_accepted": False}


def process_fields(raw, safe):
    require(set(raw) == {"command", "process", "kernel_policy"}
            and type(raw["command"]) is list and all(type(s) is str for s in raw["command"])
            and type(raw["kernel_policy"]) is dict)
    value = raw["process"]
    require(type(value) is dict and set(value) == {"process", "outcome", "started",
            "stdout_bytes", "stderr_bytes", "accepted"} and value["accepted"] is False)
    inner = value["process"]
    require(type(inner) is dict and set(inner) == {"command", "cwd", "exit_code", "stdout",
            "stderr", "duration_ms", "passed", "accepted"} and inner["accepted"] is False)
    require(type(inner["command"]) is list and all(type(s) is str for s in inner["command"])
            and all(type(inner[k]) is str for k in ("cwd", "stdout", "stderr")))
    require(type(value["outcome"]) is str)
    started, passed = boolean(value["started"]), boolean(inner["passed"])
    code = integer(inner["exit_code"], -255, 255)
    duration = integer(inner["duration_ms"], 0, MAX_DURATION_MS)
    for key in ("stdout_bytes", "stderr_bytes"):
        integer(value[key], 0, 8 * 1024**2)
    outcome = value["outcome"] if value["outcome"] in OUTCOMES else UNKNOWN
    if outcome in OUTCOMES:
        require(passed == (outcome == "SUCCEEDED"))
        if outcome == "SUCCEEDED":
            require(started and code == 0)
        if outcome == "FAILED":
            require(started and code != 0)
    kernel = raw["kernel_policy"]
    enforced = boolean(kernel["kernel_enforced"]) if "kernel_enforced" in kernel else UNKNOWN
    safe.update(outcome=outcome, started=started, process_passed=passed, exit_code=code,
        # -1 with started=False is a cancellation/spawn sentinel, NOT SIGHUP.
        signal_number=-code if started and -64 <= code < 0 else UNKNOWN,
        duration_ms=duration, kernel_enforced=enforced)


def resource_fields(raw, safe):
    require(set(raw) <= RESOURCE_FIELDS and raw.get("schema") == "bie.chromium-resource-boundary/1"
            and raw.get("kind") == "actual-paint")
    if "accepted" in raw:
        require(raw["accepted"] is False)
    if "command" in raw:
        require(type(raw["command"]) is list and all(type(s) is str for s in raw["command"]))
    for key in ("process_passed", "security_policy_weakened", "owned_processes_reaped", "owned_cgroup_removed"):
        if key in raw:
            safe[key] = boolean(raw[key])
    if "failure" in raw:
        value = raw["failure"]
        require(value is None or type(value) is str)
        safe["failure_code"] = "NONE_RECORDED" if value is None else FAILURE_CODES.get(value, "UNCLASSIFIED")
    if "kernel" in raw:
        require(type(raw["kernel"]) is dict)
        if "kernel_enforced" in raw["kernel"]:
            safe["kernel_enforced"] = boolean(raw["kernel"]["kernel_enforced"])
    if "physical_memory_bytes" in raw:
        require(integer(raw["physical_memory_bytes"]) == 2 * 1024**3)
        safe["physical_memory_bytes"] = raw["physical_memory_bytes"]
    if "swap_max" in raw:
        require(integer(raw["swap_max"]) == 0)
        safe["swap_max_bytes"] = raw["swap_max"]
    if "memory_cgroup" in raw:
        group = raw["memory_cgroup"]
        require(type(group) is dict and set(group) <= {"memory_max", "swap_max", "pids_max",
            "memory_peak", "memory_events", "events", "controller_configuration_changed", "host_supervisor_inside_workload"})
        for key, dest, expected in (("memory_max", "physical_memory_bytes", 2 * 1024**3),
                ("swap_max", "swap_max_bytes", 0), ("pids_max", "pids_max", 128)):
            if key in group:
                require(integer(group[key]) == expected and safe[dest] in (UNKNOWN, expected))
                safe[dest] = group[key]
        if "memory_peak" in group:
            safe["memory_peak_bytes"] = integer(group["memory_peak"], 0, 1024**4)
        if "memory_events" in group:
            require(type(group["memory_events"]) is dict)
            for key in EVENTS:
                if key in group["memory_events"]:
                    safe["memory_events"][key] = integer(group["memory_events"][key])


def is_safe_diagnostic(value):
    """Closed output admission: even an erroneous sanitizer cannot export extras."""
    try:
        require(type(value) is dict and set(value) == set(empty(UNKNOWN, UNKNOWN)))
        require(value["schema"] == SCHEMA and value["phase"] == "REAL_GENERATED_CONSUMER"
                and value["family"] in FAMILIES | {UNKNOWN} and value["preference"] in PREFERENCES | {UNKNOWN})
        for key in ("render_passed", "accepted", "product_accepted"):
            require(value[key] is False)
        count, timeout = value["planned_frame_count"], value["configured_timeout_s"]
        require((count == UNKNOWN and timeout == UNKNOWN) or
                (integer(count, 1, 864000) and timeout == max(120, min(3600, count * 4)) and type(timeout) is int))
        template = empty(UNKNOWN, UNKNOWN)
        for section in ("process", "resource"):
            row = value[section]
            require(type(row) is dict and set(row) == set(template[section]) and row["receipt_state"] in STATES)
            for key in ("started", "process_passed", "kernel_enforced", "security_policy_weakened",
                    "owned_processes_reaped", "owned_cgroup_removed"):
                if key in row:
                    require(row[key] == UNKNOWN or type(row[key]) is bool)
            if row["receipt_state"] != "VALID":
                for key, item in row.items():
                    if key == "memory_events":
                        require(type(item) is dict and all(v == UNKNOWN for v in item.values()))
                    elif key != "receipt_state":
                        require(item == UNKNOWN)
        p, r = value["process"], value["resource"]
        require(p["outcome"] in OUTCOMES | {UNKNOWN})
        for key, low, high in (("exit_code", -255, 255), ("signal_number", 1, 64),
                ("duration_ms", 0, MAX_DURATION_MS)):
            require(p[key] == UNKNOWN or integer(p[key], low, high) == p[key])
        if p["signal_number"] != UNKNOWN:
            require(p["started"] is True and p["exit_code"] == -p["signal_number"])
        if p["outcome"] in OUTCOMES:
            require(p["process_passed"] is (p["outcome"] == "SUCCEEDED"))
        require(r["failure_code"] in set(FAILURE_CODES.values()) | {UNKNOWN, "UNCLASSIFIED", "NONE_RECORDED"})
        require(type(r["memory_events"]) is dict and set(r["memory_events"]) == set(EVENTS))
        for counter in r["memory_events"].values():
            require(counter == UNKNOWN or integer(counter) == counter)
        for key, expected in (("physical_memory_bytes", 2 * 1024**3), ("swap_max_bytes", 0), ("pids_max", 128)):
            require(r[key] == UNKNOWN or (type(r[key]) is int and r[key] == expected))
        require(r["memory_peak_bytes"] == UNKNOWN or integer(r["memory_peak_bytes"], 0, 1024**4) == r["memory_peak_bytes"])
        return True
    except Exception:
        return False


def capture_paint_diagnostic(owned_root, *, family, preference, frame_count, duration_ms, fps):
    """Exception-safe snapshot BEFORE cleanup; the caller still re-raises paint."""
    result = empty(family if type(family) is str and family in FAMILIES else UNKNOWN,
                   preference if type(preference) is str and preference in PREFERENCES else UNKNOWN)
    try:
        require(result["family"] != UNKNOWN and result["preference"] != UNKNOWN and isinstance(owned_root, Path))
        integer(frame_count, 1, 864000); integer(duration_ms, 1, 3600000); integer(fps, 1, 240)
        require(frame_count == (duration_ms * fps + 999) // 1000)
        result["planned_frame_count"] = frame_count
        # The unchanged real_paint invocation uses exactly this n*4 policy.
        result["configured_timeout_s"] = max(120, min(3600, frame_count * 4))
        output = owned_root / ("paint-" + preference)
        for section, name, extract in (("process", "PROCESS.json", process_fields),
                ("resource", "CHROMIUM_RESOURCE.json", resource_fields)):
            state, raw = read_receipt(owned_root, output, name)
            result[section]["receipt_state"] = state
            if state == "VALID":
                safe = dict(result[section])
                if section == "resource":
                    safe["memory_events"] = dict(safe["memory_events"])
                try:
                    extract(raw, safe)
                    result[section] = safe
                except Exception:
                    result[section]["receipt_state"] = "INVALID"
        return result if is_safe_diagnostic(result) else empty(result["family"], result["preference"])
    except Exception:
        return empty(result["family"], result["preference"])
