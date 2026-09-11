"""RE-TEMP-059 — Validate a whole TEMP integration bundle before GitHub application."""
from dataclasses import dataclass

@dataclass(frozen=True)
class BundleTask:
    task_id: str
    has_spec: bool
    has_result: bool
    has_test_result: bool
    canonical_namespace_ready: bool
    unittest_compatible: bool

def validate_bundle(tasks, expected_start=4, expected_end=59):
    xs=tuple(tasks)
    ids={t.task_id:t for t in xs}
    expected=[f"BIE-RE-TEMP-{n:03d}" for n in range(expected_start,expected_end+1)]
    missing=[x for x in expected if x not in ids]
    invalid=[]
    for tid in expected:
        t=ids.get(tid)
        if t and not (t.has_spec and t.has_result and t.has_test_result and t.canonical_namespace_ready and t.unittest_compatible):
            invalid.append(tid)
    extra=sorted(set(ids)-set(expected))
    state="READY" if not missing and not invalid else "BLOCKED"
    return {"state":state,"missing":tuple(missing),"invalid":tuple(invalid),"extra":tuple(extra)}
