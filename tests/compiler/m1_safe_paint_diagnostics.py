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


def read_receipt(root, output, name, max_bytes=MAX_INPUT_BYTES):
    """No traversal or link following; Linux opens against an anchored dir fd."""
    try:
        integer(max_bytes, 1, MAX_INPUT_BYTES)
        root_before = directory(root)
        try:
            output.lstat()
        except FileNotFoundError:
            return "ABSENT", None
        output_before = directory(output)
        path = output / name
        before = path.lstat()
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and not path.is_symlink())
        if before.st_size > max_bytes:
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
                data = stream.read(max_bytes + 1)
                require(signature(os.fstat(stream.fileno())) == signature(handle_before))
            require(signature(path.lstat()) == signature(before)
                    and directory(root) == root_before and directory(output) == output_before)
        finally:
            if dfd is not None:
                os.close(dfd)
        if len(data) > max_bytes:
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


CAPTURE_SCHEMA = "bie.task036.m1.capture-controller-observation/1"
CAPTURE_PHASES = frozenset({"REQUEST_READ", "MODULE_LOAD", "PIN_CHECK", "BUNDLE", "OPEN_BROWSER",
    "SELECT_COMPOSITION", "COMPOSITION_CHECK", "RENDER_STILL", "MEASUREMENT_CHECK", "FRAME_HASH",
    "MODE_INVENTORY", "RESTORE_INVENTORY", "RENDER_MEDIA", "MEDIA_HASH", "RESULT_WRITE", "BROWSER_CLOSE"})
CAPTURE_GUARDS = {"CAPTURE_PIN_MISMATCH": "PIN_CHECK", "CAPTURE_COMPOSITION_MISMATCH": "COMPOSITION_CHECK",
    "CAPTURE_DOM_MEASUREMENT_MISSING": "MEASUREMENT_CHECK", "CAPTURE_DOM_NONDETERMINISM": "MEASUREMENT_CHECK",
    "CAPTURE_ASSET_READINESS": "MEASUREMENT_CHECK", "CAPTURE_DOM_MODE_DRIFT": "MODE_INVENTORY",
    "CAPTURE_DOM_RESTORE_DRIFT": "RESTORE_INVENTORY"}


def empty_capture():
    return {"schema": CAPTURE_SCHEMA, "provenance": "CANONICAL_CAPTURE_CONTROLLER_FAILURE_FILE",
        "receipt_state": UNKNOWN, "controller_phase": UNKNOWN, "guard_code": UNKNOWN,
        "frame": UNKNOWN, "shot_kind": UNKNOWN, "target_index": UNKNOWN,
        "frame_count": UNKNOWN, "manifest_sha256": UNKNOWN,
        "render_passed": False, "accepted": False, "product_accepted": False}


def is_safe_capture_observation(value):
    try:
        template = empty_capture()
        require(type(value) is dict)
        keys=set(template)
        if value.get('schema')=='bie.task036.m1.capture-controller-observation/2':keys.add('policy_calls')
        require(set(value)==keys)
        require(type(value["schema"]) is str and value["schema"] in {CAPTURE_SCHEMA,"bie.task036.m1.capture-controller-observation/2"} and value["provenance"] == template["provenance"]
            and value["receipt_state"] in STATES)
        require(all(value[key] is False for key in ("render_passed", "accepted", "product_accepted")))
        if value['schema']=='bie.task036.m1.capture-controller-observation/2':require(value['receipt_state']=='VALID')
        keys = ("controller_phase", "guard_code", "frame", "shot_kind", "target_index", "frame_count", "manifest_sha256")
        if value["receipt_state"] != "VALID":
            require(all(value[key] == UNKNOWN for key in keys))
        else:
            for key in ("controller_phase", "guard_code", "shot_kind", "manifest_sha256"):
                require(type(value[key]) is str and len(value[key]) <= 64)
            policy=value["schema"]=="bie.task036.m1.capture-controller-observation/2"
            policy_guards={
                "MEDIA_POLICY_CREATE":{"POLICY_SHAPE","POLICY_IDENTITY"},
                "MEDIA_CALLBACK_PRE":{"REQUEST_SHAPE","ARGUMENT_SHAPE","ARGUMENT_THREADS","ARGUMENT_INPUT","ARGUMENT_OUTPUT","ARGUMENT_CODEC","ARGUMENT_PIPE","CALLBACK_DUPLICATE"},
                "MEDIA_CALLBACK_STITCH":{"REQUEST_SHAPE","ARGUMENT_SHAPE","ARGUMENT_THREADS","ARGUMENT_INPUT","ARGUMENT_OUTPUT","ARGUMENT_CODEC","CALLBACK_DUPLICATE"},
                "MEDIA_CALLBACK_UNKNOWN":{"REQUEST_SHAPE","CALLBACK_KIND"},
                "MEDIA_POLICY_COMPLETE":{"COMPLETION_COUNTS"}}
            require(value["controller_phase"] in (policy_guards if policy else CAPTURE_PHASES))
            if policy:
                calls=value['policy_calls']
                require(type(calls) is dict and set(calls)=={'create','pre_stitcher','stitcher','unknown_callback','completion'})
                require(all(type(v) is int and 0<=v<=2 for v in calls.values()) and calls['create']==1
                    and calls['completion']<=1 and sum(calls.values())<=6)
                key={'MEDIA_POLICY_CREATE':'create','MEDIA_CALLBACK_PRE':'pre_stitcher','MEDIA_CALLBACK_STITCH':'stitcher',
                    'MEDIA_CALLBACK_UNKNOWN':'unknown_callback','MEDIA_POLICY_COMPLETE':'completion'}[value['controller_phase']]
                require(calls[key]>=1)
            code = value["guard_code"]
            require(code == "NONE_RECORDED" or (code in policy_guards[value["controller_phase"]] if policy
                else CAPTURE_GUARDS.get(code) == value["controller_phase"]))
            integer(value["frame_count"], 1, 2400)
            integer(value["frame"], -1, value["frame_count"] - 1)
            integer(value["target_index"], -1, 11999)
            require(value["shot_kind"] in {"NONE", "FULL", "BASELINE", "ISOLATED", "MUTED", "REPEAT"})
            require((value["target_index"] == -1) == (value["shot_kind"] in {"NONE", "FULL", "REPEAT"}))
            require(len(value["manifest_sha256"]) == 64 and all(c in "0123456789abcdef" for c in value["manifest_sha256"]))
        return True
    except BaseException:
        return False


def capture_controller_observation(owned_root, *, preference, manifest_sha256, frame_count):
    result = empty_capture()
    try:
        require(type(preference) is str and preference in PREFERENCES and isinstance(owned_root, Path))
        require(type(manifest_sha256) is str and len(manifest_sha256) == 64
            and all(c in "0123456789abcdef" for c in manifest_sha256))
        integer(frame_count, 1, 2400)
        state, raw = read_receipt(owned_root, owned_root / ("paint-" + preference),
            "CAPTURE_PROCESS_DIAGNOSTIC.json", max_bytes=1024)
        result["receipt_state"] = state
        if state == "VALID":
            require(type(raw) is dict)
            keys={"schema", "phase", "guard_code", "frame", "shot_kind","target_index", "frame_count", "manifest_sha256", "accepted"}
            if raw.get('schema')=='bie.capture-controller-failure/2':keys.add('policy_calls')
            require(set(raw)==keys)
            require(raw["schema"] in {"bie.capture-controller-failure/1","bie.capture-controller-failure/2"} and raw["accepted"] is False
                and raw["manifest_sha256"] == manifest_sha256 and raw["frame_count"] == frame_count)
            if raw["schema"]=="bie.capture-controller-failure/2":
                result["schema"]="bie.task036.m1.capture-controller-observation/2"
                result['policy_calls']=raw['policy_calls']
            for key in ("guard_code", "frame", "shot_kind", "target_index", "frame_count", "manifest_sha256"):
                result[key] = raw[key]
            result["controller_phase"] = raw["phase"]
            require(is_safe_capture_observation(result))
        return result
    except BaseException:
        result = empty_capture()
        result["receipt_state"] = "INVALID"
        return result


# Separate from file admission above: no private receipt file or output is read.
TYPED_SCHEMA = "bie.task036.m1.paint-process-typed-observation/1"
TYPED_STATES = frozenset({"VALID", "INVALID", "UNAVAILABLE", UNKNOWN})
TYPED_STAGES = frozenset({"NONE", "NOT_CALLED", "CALL_RAISED", "RETURN_SHAPE",
    "PROCESS_TYPE", "PROCESS_FIELDS", "RESOURCE_FIELDS", "OBSERVER_ERROR",
    "BINDING_UNAVAILABLE", "MULTIPLE_CALLS"})


def empty_typed(stage="NOT_CALLED", verified=False):
    verified = verified is True
    stage = stage if type(stage) is str and len(stage) <= 32 and stage in TYPED_STAGES else "OBSERVER_ERROR"
    return {"schema": TYPED_SCHEMA, "phase": "REAL_GENERATED_CONSUMER",
        "provenance": "CANONICAL_WORKER_RETURN" if verified else "UNVERIFIED_TEST_RETURN",
        "capture_point": "AFTER_WORKER_RETURN_BEFORE_PROCESS_JSON",
        "call_origin_verified": verified, "observation_stage": stage,
        "process": {"availability": "UNAVAILABLE", "outcome": UNKNOWN, "started": UNKNOWN,
            "process_passed": UNKNOWN, "exit_code": UNKNOWN, "signal_number": UNKNOWN,
            "duration_ms": UNKNOWN},
        "resource": {"availability": "UNAVAILABLE", "kernel_enforced": UNKNOWN,
            "process_passed": UNKNOWN, "security_policy_weakened": UNKNOWN,
            "owned_processes_reaped": UNKNOWN, "owned_cgroup_removed": UNKNOWN,
            "memory_events": {key: UNKNOWN for key in EVENTS}, "memory_peak_bytes": UNKNOWN,
            "physical_memory_bytes": UNKNOWN, "swap_max_bytes": UNKNOWN, "pids_max": UNKNOWN},
        "render_passed": False, "accepted": False, "product_accepted": False}


def typed_process_fields(value):
    """Exact frozen types; never touch command/cwd/stdout/stderr/byte counts."""
    from bie.compiler.build_common import ProcessReceipt
    from bie.compiler.render_process import RenderProcessResult
    require(type(value) is RenderProcessResult and type(value.process) is ProcessReceipt)
    inner = value.process
    require(value.accepted is False and inner.accepted is False)
    require(type(value.outcome) is str and len(value.outcome) <= 32)
    outcome = value.outcome if value.outcome in OUTCOMES else UNKNOWN
    started, passed = boolean(value.started), boolean(inner.passed)
    code = integer(inner.exit_code, -255, 255)
    duration = integer(inner.duration_ms, 0, MAX_DURATION_MS)
    if outcome in OUTCOMES:
        require(passed == (outcome == "SUCCEEDED"))
        if outcome == "SUCCEEDED":
            require(started and code == 0)
        if outcome == "FAILED":
            require(started and code != 0)
        if outcome in {"SPAWN_ERROR", "TIMED_OUT", "OUTPUT_LIMIT"}:
            require(started == (outcome != "SPAWN_ERROR"))
    return {"availability": "VALID", "outcome": outcome, "started": started,
        "process_passed": passed, "exit_code": code,
        "signal_number": -code if started and -64 <= code < 0 else UNKNOWN,
        "duration_ms": duration}


def typed_resource_fields(kernel):
    """Read fixed scalar keys only, not entire kernel/driver/grant structures."""
    require(type(kernel) is dict)
    safe = empty_typed()["resource"]
    if "kernel_enforced" in kernel:
        safe["kernel_enforced"] = boolean(kernel["kernel_enforced"])
    if "chromium_resource_boundary" not in kernel:
        safe["availability"] = UNKNOWN
        return safe
    boundary = kernel["chromium_resource_boundary"]
    require(type(boundary) is dict
        and type(boundary.get("schema")) is str and boundary["schema"] == "bie.chromium-resource-boundary/1"
        and type(boundary.get("kind")) is str and boundary["kind"] == "actual-paint")
    if "accepted" in boundary:
        require(boundary["accepted"] is False)
    for key in ("process_passed", "security_policy_weakened", "owned_processes_reaped", "owned_cgroup_removed"):
        if key in boundary:
            safe[key] = boolean(boundary[key])
    for key, dest, expected in (("physical_memory_bytes", "physical_memory_bytes", 2 * 1024**3),
            ("swap_max", "swap_max_bytes", 0)):
        if key in boundary:
            require(integer(boundary[key]) == expected)
            safe[dest] = boundary[key]
    # This is the same fixed memory-cgroup summary returned by the worker.
    if "memory_cgroup" in boundary:
        group = boundary["memory_cgroup"]
        require(type(group) is dict)
        for key, dest, expected in (("memory_max", "physical_memory_bytes", 2 * 1024**3),
                ("swap_max", "swap_max_bytes", 0), ("pids_max", "pids_max", 128)):
            if key in group:
                require(integer(group[key]) == expected and safe[dest] in (UNKNOWN, expected))
                safe[dest] = group[key]
        if "memory_peak" in group:
            safe["memory_peak_bytes"] = integer(group["memory_peak"], 0, 1024**4)
        if "memory_events" in group:
            events = group["memory_events"]
            require(type(events) is dict)
            for key in EVENTS:
                if key in events:
                    safe["memory_events"][key] = integer(events[key])
    safe["availability"] = "VALID"
    return safe


def project_typed_return(returned, *, verified=False):
    """Immediate scalar projection; the original objects are never retained."""
    safe = empty_typed("NONE", verified)
    if type(returned) is not tuple or len(returned) != 2:
        return empty_typed("RETURN_SHAPE", verified)
    try:
        from bie.compiler.build_common import ProcessReceipt
        from bie.compiler.render_process import RenderProcessResult
        require(type(returned[0]) is RenderProcessResult and type(returned[0].process) is ProcessReceipt)
    except Exception:
        safe["process"]["availability"] = "INVALID"
        safe["observation_stage"] = "PROCESS_TYPE"
    else:
        try:
            safe["process"] = typed_process_fields(returned[0])
        except Exception:
            safe["process"]["availability"] = "INVALID"
            safe["observation_stage"] = "PROCESS_FIELDS"
    try:
        safe["resource"] = typed_resource_fields(returned[1])
        if safe["process"]["availability"] == "VALID" and safe["resource"]["process_passed"] != UNKNOWN:
            require(safe["resource"]["process_passed"] is safe["process"]["process_passed"])
    except Exception:
        safe["resource"] = empty_typed()["resource"]
        safe["resource"]["availability"] = "INVALID"
        if safe["observation_stage"] == "NONE":
            safe["observation_stage"] = "RESOURCE_FIELDS"
    return safe if is_safe_typed_observation(safe) else empty_typed("OBSERVER_ERROR", verified)


def typed_unknown(value):
    return type(value) is str and value == UNKNOWN


def is_safe_typed_observation(value):
    """Closed scalar-only schema, independent of the historical JSON diagnostics."""
    try:
        template = empty_typed()
        require(type(value) is dict and len(value) == len(template)
            and all(type(k) is str and len(k) <= 64 for k in value) and set(value) == set(template))
        require(all(type(value[k]) is str for k in ("schema", "phase", "capture_point", "provenance")))
        require(value["schema"] == TYPED_SCHEMA and value["phase"] == template["phase"]
            and value["capture_point"] == template["capture_point"])
        require(type(value["call_origin_verified"]) is bool
            and value["provenance"] == empty_typed(verified=value["call_origin_verified"])["provenance"])
        require(type(value["observation_stage"]) is str and len(value["observation_stage"]) <= 32
            and value["observation_stage"] in TYPED_STAGES)
        for key in ("accepted", "product_accepted", "render_passed"):
            require(value[key] is False)
        for section in ("process", "resource"):
            row = value[section]
            require(type(row) is dict and len(row) == len(template[section])
                and all(type(k) is str and len(k) <= 64 for k in row) and set(row) == set(template[section])
                and type(row["availability"]) is str and len(row["availability"]) <= 16
                and row["availability"] in TYPED_STATES)
            for key in ("started", "process_passed", "kernel_enforced", "security_policy_weakened",
                    "owned_processes_reaped", "owned_cgroup_removed"):
                if key in row:
                    require(typed_unknown(row[key]) or type(row[key]) is bool)
            if row["availability"] in {"INVALID", "UNAVAILABLE", UNKNOWN}:
                for key, item in row.items():
                    if key == "memory_events":
                        require(type(item) is dict and len(item) == len(EVENTS)
                            and all(type(k) is str for k in item) and set(item) == set(EVENTS)
                            and all(typed_unknown(v) for v in item.values()))
                    elif section == "resource" and row["availability"] == UNKNOWN and key == "kernel_enforced":
                        pass  # Root kernel flag may exist without the boundary summary.
                    elif key != "availability":
                        require(typed_unknown(item))
        p, r = value["process"], value["resource"]
        require(p["availability"] != UNKNOWN)
        if value["observation_stage"] == "NONE":
            require(p["availability"] == "VALID" and r["availability"] in {"VALID", UNKNOWN})
        if value["observation_stage"] in {"PROCESS_TYPE", "PROCESS_FIELDS"}:
            require(p["availability"] == "INVALID")
        if value["observation_stage"] == "RESOURCE_FIELDS":
            require(p["availability"] == "VALID" and r["availability"] == "INVALID")
        require(type(p["outcome"]) is str and len(p["outcome"]) <= 32 and p["outcome"] in OUTCOMES | {UNKNOWN})
        for key, low, high in (("exit_code", -255, 255), ("signal_number", 1, 64),
                ("duration_ms", 0, MAX_DURATION_MS)):
            require(typed_unknown(p[key]) or integer(p[key], low, high) == p[key])
        if p["signal_number"] != UNKNOWN:
            require(p["started"] is True and p["exit_code"] == -p["signal_number"])
        if p["outcome"] in OUTCOMES:
            require(p["availability"] == "VALID" and p["process_passed"] is (p["outcome"] == "SUCCEEDED"))
            if p["outcome"] == "SUCCEEDED":
                require(p["started"] is True and p["exit_code"] == 0)
            if p["outcome"] == "FAILED":
                require(p["started"] is True and p["exit_code"] != 0)
        if p["availability"] == "VALID":
            boolean(p["started"]); boolean(p["process_passed"])
            integer(p["exit_code"], -255, 255); integer(p["duration_ms"], 0, MAX_DURATION_MS)
        if value["observation_stage"] in {"NOT_CALLED", "CALL_RAISED", "RETURN_SHAPE",
                "OBSERVER_ERROR", "BINDING_UNAVAILABLE", "MULTIPLE_CALLS"}:
            require(p["availability"] == r["availability"] == "UNAVAILABLE")
        require(type(r["memory_events"]) is dict and len(r["memory_events"]) == len(EVENTS)
            and all(type(k) is str for k in r["memory_events"]) and set(r["memory_events"]) == set(EVENTS))
        for counter in r["memory_events"].values():
            require(typed_unknown(counter) or integer(counter) == counter)
        for key, expected in (("physical_memory_bytes", 2 * 1024**3), ("swap_max_bytes", 0), ("pids_max", 128)):
            require(typed_unknown(r[key]) or (type(r[key]) is int and r[key] == expected))
        require(typed_unknown(r["memory_peak_bytes"]) or integer(r["memory_peak_bytes"], 0, 1024**4) == r["memory_peak_bytes"])
        if p["availability"] == "VALID" and type(r["process_passed"]) is bool:
            require(r["process_passed"] is p["process_passed"])
        return True
    except Exception:
        return False


class TypedPaintObserver:
    """Only a safe scalar record survives a call; never its args/result/exception."""
    def __init__(self, *, verified=False):
        self._verified = verified is True
        self._called = False
        self._multiple = False
        self._safe = empty_typed(verified=self._verified)

    def delegate(self, original, *args, **kwargs):
        try:
            returned = original(*args, **kwargs)
        except BaseException:
            try:
                self._safe = empty_typed("CALL_RAISED", self._verified)
                self._called = True
            except BaseException:
                pass
            raise
        # No observation error can replace the original return or native failure.
        try:
            self._multiple = self._multiple or self._called
            self._called = True
            self._safe = (empty_typed("MULTIPLE_CALLS", self._verified) if self._multiple else
                          project_typed_return(returned, verified=self._verified))
        except BaseException:
            try:
                self._safe = empty_typed("OBSERVER_ERROR", self._verified)
            except BaseException:
                pass
        return returned

    def snapshot(self):
        # This copies only the closed, already projected safe record.
        if not is_safe_typed_observation(self._safe):
            return empty_typed("OBSERVER_ERROR", self._verified)
        value = dict(self._safe)
        value["process"] = dict(self._safe["process"])
        value["resource"] = dict(self._safe["resource"])
        value["resource"]["memory_events"] = dict(self._safe["resource"]["memory_events"])
        return value


def canonical_paint_binding():
    """Source-origin admission only; no worker invocation or private field read."""
    from types import ModuleType, FunctionType
    from bie.compiler import chromium_resource_worker as worker
    expected = Path(__file__).resolve().parents[2] / "bie/compiler/chromium_resource_worker.py"
    original = worker.run_chromium_isolated
    require(type(worker) is ModuleType and type(original) is FunctionType
        and Path(worker.__file__).resolve() == expected
        and Path(original.__code__.co_filename).resolve() == expected
        and original.__module__ == "bie.compiler.chromium_resource_worker"
        and original.__name__ == "run_chromium_isolated")
    return worker, original


def observe_paint_process():
    """Test-owned scope around the unchanged painter's locally imported call."""
    from contextlib import contextmanager

    @contextmanager
    def scope():
        observer = None
        try:
            observer = TypedPaintObserver()
            worker, original = canonical_paint_binding()
            observer._verified = True
            observer._safe = empty_typed(verified=True)
        except BaseException:
            try:
                if observer is not None:
                    observer._safe = empty_typed("BINDING_UNAVAILABLE")
            except BaseException:
                pass
            yield observer
            return

        def observed(*args, **kwargs):
            return observer.delegate(original, *args, **kwargs)

        worker.run_chromium_isolated = observed
        try:
            yield observer
        finally:
            worker.run_chromium_isolated = original
    return scope()


# The parent worker can reject before returning a typed result. Observe ONLY
# its fixed require codes and the exception TYPE escaping its frozen _grant
# boundary. No receipt/file/message, call argument, result or traceback is read.
GUARD_SCHEMA = "bie.task036.m1.paint-worker-guard-observation/1"
GUARD_CODES = frozenset({
    "ARGS", "DUPLICATE_ARG", "REQUIRED_ARG", "HEADLESS_ARG", "PROFILE_ARG",
    "CONTROL_SIZE", "MOUNTINFO", "EXECUTABLE_MAPPING", "EXECUTABLE_MAPPING_MOUNT",
    "EXECUTABLE_MAPPING_WRITABLE", "EXECUTABLE_MAPPING_EMPTY", "ADMISSION_STOP",
    "FOREIGN_PROCESS", "FREEZE_DEADLINE", "CLEANUP_IDENTITY", "CLEANUP_DEADLINE",
    "ENTRY_NOT_STOPPED", "PARENT_COMMAND", "EXECUTABLE_IDENTITY", "ENTRY_CHANGED",
    "POLICY_CHANGED", "ENTRY_SECURITY", "ENTRY_ENVIRONMENT", "OWNED_SANDBOX_ROOT",
    "PARENT_LIMIT", "ENTRY_LIMIT", "ENTRY_NAMESPACE", "GRANT_SCOPE", "PID_IDENTITY",
    "DRIVER_ADMISSION", "HOST_DEADLINE", "PROCESS_BOUND", "GRANT_BOUND", "CHROME_LIMIT",
    "DRIVER_RESULT", "DRIVER_EXIT", "KERNEL_POLICY", "NO_BROWSER_ADMISSION",
    "FULL_RESERVATION_NOT_OBSERVED", "ENGINE_CHANGED_AFTER_RUN", "MISSING_RESULT",
    "MEMORY_EXHAUSTED",
})
GUARD_ERROR_CODES = frozenset({"COMPILER_QA_ERROR", "FILE_NOT_FOUND", "PROCESS_LOOKUP",
    "PERMISSION_ERROR", "OS_ERROR", "VALUE_ERROR", "TYPE_ERROR", "KEY_ERROR",
    "TIMEOUT_EXPIRED", "UNICODE_DECODE_ERROR", "MEMORY_ERROR", "INTERRUPTED"})


def empty_guard(verified=False, availability="UNAVAILABLE"):
    return {"schema": GUARD_SCHEMA, "phase": "REAL_GENERATED_CONSUMER",
        "provenance": "CANONICAL_PARENT_REQUIRE_AND_BROWSER_ADMISSION",
        "call_origin_verified": verified is True, "availability": availability,
        "static_guard_rejections": UNKNOWN, "last_static_guard_code": UNKNOWN,
        "unclassified_guard_rejections": UNKNOWN, "browser_admission_calls": UNKNOWN,
        "last_browser_admission_outcome": UNKNOWN, "browser_admission_exception": UNKNOWN,
        "scope": "OBSERVED_PARENT_BOUNDARIES_NOT_INNER_PROCESS_VERDICT",
        "render_passed": False, "accepted": False, "product_accepted": False}


def is_safe_guard_observation(value):
    try:
        template = empty_guard()
        require(type(value) is dict and len(value) == len(template)
            and all(type(k) is str and len(k) <= 64 for k in value) and set(value) == set(template))
        for key in ("schema", "phase", "provenance", "scope"):
            require(type(value[key]) is str and value[key] == template[key])
        require(type(value["call_origin_verified"]) is bool)
        require(type(value["availability"]) is str and value["availability"] in {"VALID", "UNAVAILABLE", "INVALID"})
        for key in ("render_passed", "accepted", "product_accepted"):
            require(value[key] is False)
        for key in ("static_guard_rejections", "unclassified_guard_rejections", "browser_admission_calls"):
            require(typed_unknown(value[key]) or integer(value[key], 0, 1024) == value[key])
        for key, allowed in (("last_static_guard_code", GUARD_CODES),
            ("last_browser_admission_outcome", {"NOT_CALLED", "RETURNED", "RAISED"}),
            ("browser_admission_exception", GUARD_ERROR_CODES)):
            require(type(value[key]) is str and len(value[key]) <= 64 and value[key] in allowed | {UNKNOWN})
        if value["availability"] == "VALID":
            require(value["call_origin_verified"] is True)
            for key in ("static_guard_rejections", "unclassified_guard_rejections", "browser_admission_calls"):
                integer(value[key], 0, 1024)
            require((value["static_guard_rejections"] == 0) is typed_unknown(value["last_static_guard_code"]))
            if value["browser_admission_calls"] == 0:
                require(value["last_browser_admission_outcome"] == "NOT_CALLED")
            else:
                require(value["last_browser_admission_outcome"] in {"RETURNED", "RAISED"})
            if value["last_browser_admission_outcome"] != "RAISED":
                require(typed_unknown(value["browser_admission_exception"]))
        else:
            for key in ("static_guard_rejections", "unclassified_guard_rejections", "browser_admission_calls",
                        "last_static_guard_code", "last_browser_admission_outcome", "browser_admission_exception"):
                require(typed_unknown(value[key]))
        return True
    except BaseException:
        return False


def guard_exception_code(error_type):
    from subprocess import TimeoutExpired
    from bie.compiler.qa_common import CompilerQAError
    # Exact class identity, not __name__, str, repr, args or exception attributes.
    return {CompilerQAError: "COMPILER_QA_ERROR", FileNotFoundError: "FILE_NOT_FOUND",
        ProcessLookupError: "PROCESS_LOOKUP", PermissionError: "PERMISSION_ERROR", OSError: "OS_ERROR",
        ValueError: "VALUE_ERROR", TypeError: "TYPE_ERROR", KeyError: "KEY_ERROR",
        TimeoutExpired: "TIMEOUT_EXPIRED", UnicodeDecodeError: "UNICODE_DECODE_ERROR",
        MemoryError: "MEMORY_ERROR", KeyboardInterrupt: "INTERRUPTED"}.get(error_type, UNKNOWN)


class WorkerGuardObserver:
    def __init__(self, verified=False):
        self._safe = empty_guard(verified)
        if verified is True:
            self._safe.update(availability="VALID", static_guard_rejections=0,
                unclassified_guard_rejections=0, browser_admission_calls=0,
                last_browser_admission_outcome="NOT_CALLED")

    def _invalid(self):
        self._safe = empty_guard(self._safe["call_origin_verified"], "INVALID")

    def delegate_require(self, original, condition, code):
        try:
            return original(condition, code)
        except BaseException:
            try:
                if self._safe["availability"] == "VALID" and type(condition) is bool and condition is False:
                    known = type(code) is str and len(code) <= 64 and code in GUARD_CODES
                    key = "static_guard_rejections" if known else "unclassified_guard_rejections"
                    count = integer(self._safe[key] + 1, 0, 1024)
                    self._safe[key] = count
                    if known:
                        self._safe["last_static_guard_code"] = code
            except BaseException:
                try: self._invalid()
                except BaseException: pass
            raise

    def delegate_grant(self, original, *args, **kwargs):
        # Count only calls, never examine or retain the PID/path/command args.
        try:
            if self._safe["availability"] == "VALID":
                self._safe["browser_admission_calls"] = integer(self._safe["browser_admission_calls"] + 1, 0, 1024)
        except BaseException:
            try: self._invalid()
            except BaseException: pass
        try:
            returned = original(*args, **kwargs)
        except BaseException as error:
            try:
                if self._safe["availability"] == "VALID":
                    self._safe["last_browser_admission_outcome"] = "RAISED"
                    self._safe["browser_admission_exception"] = guard_exception_code(type(error))
            except BaseException:
                try: self._invalid()
                except BaseException: pass
            raise
        try:
            if self._safe["availability"] == "VALID":
                self._safe["last_browser_admission_outcome"] = "RETURNED"
                self._safe["browser_admission_exception"] = UNKNOWN
        except BaseException:
            try: self._invalid()
            except BaseException: pass
        return returned

    def snapshot(self):
        return dict(self._safe) if is_safe_guard_observation(self._safe) else empty_guard(availability="INVALID")


def canonical_guard_binding():
    from types import ModuleType, FunctionType
    from bie.compiler import chromium_resource_worker as worker
    expected = Path(__file__).resolve().parents[2] / "bie/compiler/chromium_resource_worker.py"
    require(type(worker) is ModuleType and Path(worker.__file__).resolve() == expected)
    for name in ("require", "_grant"):
        original = getattr(worker, name)
        require(type(original) is FunctionType and Path(original.__code__.co_filename).resolve() == expected
            and original.__module__ == "bie.compiler.chromium_resource_worker" and original.__name__ == name)
    return worker, worker.require, worker._grant


def observe_worker_rejections():
    from contextlib import contextmanager

    @contextmanager
    def scope():
        observer = None
        try:
            worker, original_require, original_grant = canonical_guard_binding()
            observer = WorkerGuardObserver(verified=True)
        except BaseException:
            yield observer
            return

        def observed_require(condition, code):
            return observer.delegate_require(original_require, condition, code)

        def observed_grant(*args, **kwargs):
            return observer.delegate_grant(original_grant, *args, **kwargs)

        worker.require, worker._grant = observed_require, observed_grant
        try:
            yield observer
        finally:
            worker.require, worker._grant = original_require, original_grant
    return scope()
