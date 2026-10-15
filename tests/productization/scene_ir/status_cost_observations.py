"""Read-only cost of a *failed* child's committed store, not a child retry.

Only fixed repository method names, counts and CPU durations leave this scope.
This never changes the primary smoke verdict, budget, fixture or stage state.
The separate parent read is not proof that the bounded child completed.
"""
import cProfile
from hashlib import sha256
from math import isfinite
from pathlib import Path
import re
import sys
import time
from types import CodeType

from bie.productization.contracts import canonical

SCHEMA = "bie.task036.failed-child-status-cost/1"
ROOT = Path(__file__).resolve().parents[3]
METHODS = {
    "bie/productization/scene_ir_slice.py": frozenset({"status", "_completed_status_bundle",
        "_verified_scene_bundle", "verified_animation_with_inputs"}),
    "bie/productization/pedagogy_slice.py": frozenset({"status", "verified_pedagogy",
        "components", "pedagogy_inputs"}),
    "bie/productization/math_slice.py": frozenset({"status", "verified_math", "upstream"}),
    "bie/productization/director_slice.py": frozenset({"verified_director", "request"}),
    "bie/productization/visual_slice.py": frozenset({"verified_visual", "current_inputs"}),
    "bie/productization/animation_slice.py": frozenset({"verified_animation", "animation_inputs"}),
    "bie/compiler/producer_motion_admission.py": frozenset({"_snapshot", "current_motion_admission"}),
    "bie/productization/scene_ir_m1_review.py": frozenset({"verified_m1_review",
        "verified_source_chain", "read_regular"}),
}
EXCEPTIONS = {ValueError: "ValueError", TypeError: "TypeError", RuntimeError: "RuntimeError",
    AssertionError: "AssertionError", PermissionError: "PermissionError",
    FileNotFoundError: "FileNotFoundError", MemoryError: "MemoryError"}


def milliseconds(value):
    if type(value) not in (float, int) or not isfinite(value) or not 0 <= value <= 120:
        return None
    return round(value * 1000)


def project_stats(profile):
    """Do not stringify builtin code entries, caller graphs, arguments or objects."""
    result = []
    entries = profile.getstats()
    if type(entries) is not list or len(entries) > 8192:
        raise ValueError("STATUS_COST_STATS")
    for entry in entries:
        code = entry.code
        if type(code) is not CodeType:
            continue
        path = Path(code.co_filename)
        if not path.is_absolute():
            continue
        try:
            relative = path.resolve().relative_to(ROOT).as_posix()
        except ValueError:
            continue
        if code.co_name not in METHODS.get(relative, ()):
            continue
        calls = entry.callcount
        own, cumulative = milliseconds(entry.inlinetime), milliseconds(entry.totaltime)
        if type(calls) is not int or not 0 < calls <= 1000000 or own is None or cumulative is None:
            raise ValueError("STATUS_COST_VALUE")
        result.append(dict(source=relative, function=code.co_name, calls=calls,
            exclusive_cpu_ms=own, cumulative_cpu_ms=cumulative))
    if len(result) > 64 or len({(r["source"], r["function"]) for r in result}) != len(result):
        raise ValueError("STATUS_COST_IDENTITIES")
    return sorted(result, key=lambda row: (row["source"], row["function"]))


def observe(service, run, tenant, saved, queues):
    """One actual status read after first-child reap, before owned-store cleanup.

    Exceptions and diagnostic failure cannot replace the original smoke failure.
    Profiling adds overhead to this parent observation, not to the failed child.
    No result or authority is reused by production or the positive journey.
    """
    result = dict(schema=SCHEMA, scope="FAILED_CHILD_PARENT_READ_ONLY",
        outcome="NOT_ADMITTED", exception_class="UNKNOWN", cpu_ms=None,
        methods=[], dependencies=[], state_unchanged=None, queue_unchanged=None,
        profile_restored=None, reader_called=False, observation_complete=False,
        original_child_passed=False, product_accepted=False)
    profile = None
    returned = False
    diagnostic_failed = False
    prior = sys.getprofile()
    try:
        from bie.productization.scene_ir_slice import SceneIRProducerService, STAGES
        if not isinstance(service, SceneIRProducerService) or prior is not None:
            return result
        if type(queues) is not dict or type(queues.get("ACKED")) is not int or queues["ACKED"] != 11:
            return result
        if any(type(v) is not int or v < 0 for v in queues.values()) or sum(queues.values()) != 11:
            return result
        if any(saved["stages"][stage]["attempts"][-1]["state"] != "SUCCEEDED" for stage in STAGES):
            return result
        before = canonical(saved)
        dependencies = []
        for stage in ("VISUAL", "ANIMATION", "DIRECTOR", "SCENE_IR"):
            aid, record = service.stage_ref(run, stage)
            if (type(aid) is not str or re.fullmatch(r"[A-Za-z0-9:_-]{1,256}", aid) is None
                    or type(record.blob_digest) is not str
                    or re.fullmatch(r"[a-f0-9]{64}", record.blob_digest) is None):
                raise ValueError("STATUS_COST_REFERENCE")
            # No caller/tamper-controlled reference text is ever exported.
            dependencies.append(dict(stage=stage,
                reference_sha256=sha256(aid.encode("utf-8")).hexdigest(), sha256=record.blob_digest))
        result["outcome"] = "UNAVAILABLE"
        profile = cProfile.Profile(timer=time.process_time)
        started = time.process_time()
        try:
            profile.enable()
            result["reader_called"] = True
            try:
                value = service.status(run, tenant)
                returned = True
                result["outcome"] = ("RETURNED" if type(value) is dict
                    and type(value.get("stages")) is dict
                    and set(value["stages"]) == set(STAGES)
                    and all(v == "SUCCEEDED" for v in value["stages"].values()) else "INVALID_RETURN")
            except BaseException as error:
                result["outcome"] = "RAISED"
                result["exception_class"] = EXCEPTIONS.get(type(error), "UNKNOWN")
        finally:
            try: profile.disable()
            except BaseException: diagnostic_failed = True
            result["cpu_ms"] = milliseconds(time.process_time() - started)
        result["methods"] = project_stats(profile)
        result["state_unchanged"] = canonical(service.persistence.load_run_state(run)) == before
        result["queue_unchanged"] = service.queue.stats() == queues
        if not result["state_unchanged"] or not result["queue_unchanged"]:
            result["outcome"] = "STATE_CHANGED"
        elif returned and result["outcome"] == "RETURNED":
            # Publish only hashes, and only after the native status read and
            # both unchanged-store checks. Never turn these into authority.
            result["dependencies"] = dependencies
        result["observation_complete"] = not diagnostic_failed
    except BaseException as error:
        if result["outcome"] != "RAISED":
            result["outcome"] = "UNAVAILABLE"
        diagnostic_failed = True
    finally:
        try:
            if profile is not None:
                try: profile.disable()
                except BaseException: diagnostic_failed = True
            # A partially enabled or broken profiler must not remain installed.
            if sys.getprofile() is not prior:
                sys.setprofile(prior)
            result["profile_restored"] = sys.getprofile() is prior
        except BaseException:
            result["profile_restored"] = None
            diagnostic_failed = True
        if diagnostic_failed:
            result["observation_complete"] = False
            if result["outcome"] == "RETURNED":
                result["outcome"] = "UNAVAILABLE"
    return result
