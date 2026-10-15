"""Test-only phase evidence for the unchanged H4 publication fixture.

The native repair API intentionally converts some exceptions to a blocked result.
Record which delegated operation raised, never its messages, arguments or result.
The existing unittest outcome remains authoritative. No renderer is replaced.
"""
from contextlib import contextmanager, ExitStack
from pathlib import Path
from types import FunctionType
from unittest.mock import patch

SCHEMA = "bie.task036.m1.h4-operation-observation/1"
ROOT = Path(__file__).resolve().parents[2]
PHASES = ("PROBE_CONSTRUCT", "PROBE_ENTER", "CANDIDATES", "PROBE_MEASURE", "PROBE_EXIT")


def new_state():
    return dict(schema=SCHEMA, available=False, complete=True, bindings_restored=None,
        phases={key: dict(calls=0, returned=0, raised=0) for key in PHASES},
        exceptions=[], accepted=False, product_accepted=False)


def exception_name(error):
    from bie.compiler.qa_common import CompilerQAError
    allowed = ((CompilerQAError, "CompilerQAError"), (ValueError, "ValueError"),
        (TypeError, "TypeError"), (RuntimeError, "RuntimeError"), (AssertionError, "AssertionError"),
        (PermissionError, "PermissionError"), (FileNotFoundError, "FileNotFoundError"),
        (TimeoutError, "TimeoutError"), (OSError, "OSError"), (MemoryError, "MemoryError"))
    return next((name for cls, name in allowed if type(error) is cls), "UNKNOWN")


def note(state, phase, event, error=None):
    try:
        row = state["phases"][phase]
        key = {"CALL": "calls", "RETURN": "returned", "RAISE": "raised"}[event]
        if row[key] >= 64:
            state["complete"] = False
            return
        row[key] += 1
        if event == "RAISE":
            if len(state["exceptions"]) >= 8:
                state["complete"] = False
            else:
                state["exceptions"].append(dict(phase=phase, exception_class=exception_name(error),
                    structured_code="UNKNOWN"))
    except BaseException:
        # No failed observation can replace a native return or exception.
        state["complete"] = False


def wrapper(original, phase, state):
    def delegated(*args, **kwargs):
        try: note(state, phase, "CALL")
        except BaseException: state["complete"] = False
        try:
            result = original(*args, **kwargs)
        except BaseException as error:
            try: note(state, phase, "RAISE", error)
            except BaseException: state["complete"] = False
            raise
        try: note(state, phase, "RETURN")
        except BaseException: state["complete"] = False
        return result
    return delegated


def restore(stack, bindings, state):
    try:
        stack.close()
    except BaseException:
        state["complete"] = False
    # Explicit fallback restoration after a failed diagnostic context teardown.
    # These are only the exact bindings this observer captured, never new code.
    for owner, name, original in reversed(bindings):
        try:
            if getattr(owner, name) is not original:
                setattr(owner, name, original)
        except BaseException:
            state["complete"] = False
    try:
        state["bindings_restored"] = all(getattr(owner, name) is original for owner, name, original in bindings)
    except BaseException:
        state["bindings_restored"] = None


@contextmanager
def capture(root=ROOT):
    state = new_state()
    bindings = []
    stack = ExitStack()
    try:
        from bie.compiler import layout_repair
        from bie.compiler.layout_browser import ChromiumLayoutProbe
        expected = ((layout_repair, "_run_candidates", "CANDIDATES", "bie/compiler/layout_repair.py"),
            (ChromiumLayoutProbe, "__init__", "PROBE_CONSTRUCT", "bie/compiler/layout_browser.py"),
            (ChromiumLayoutProbe, "__enter__", "PROBE_ENTER", "bie/compiler/layout_browser.py"),
            (ChromiumLayoutProbe, "measure", "PROBE_MEASURE", "bie/compiler/layout_browser.py"),
            (ChromiumLayoutProbe, "__exit__", "PROBE_EXIT", "bie/compiler/layout_browser.py"))
        if Path(root).resolve() != ROOT:
            raise ValueError("H4_OBSERVER_ORIGIN")
        for owner, name, phase, relative in expected:
            original = getattr(owner, name)
            if (type(original) is not FunctionType
                    or Path(original.__code__.co_filename).resolve() != ROOT/relative):
                raise ValueError("H4_OBSERVER_ORIGIN")
            bindings.append((owner, name, original))
            stack.enter_context(patch.object(owner, name, wrapper(original, phase, state)))
        state["available"] = True
    except BaseException:
        state["complete"] = False
        # A partial install must be removed before the unchanged suite runs.
        restore(stack, bindings, state)
    try:
        yield state
    finally:
        restore(stack, bindings, state)


def snapshot(state):
    """Construct the closed external shape explicitly; never copy native objects."""
    result = new_state()
    try:
        for key in ("available", "complete", "accepted", "product_accepted"):
            if type(state[key]) is not bool:
                raise ValueError("H4_OBSERVER_TYPE")
        if state["accepted"] or state["product_accepted"]:
            raise ValueError("H4_OBSERVER_ACCEPTANCE")
        if type(state["bindings_restored"]) not in (bool, type(None)):
            raise ValueError("H4_OBSERVER_TYPE")
        result.update(available=state["available"], complete=state["complete"],
            bindings_restored=state["bindings_restored"])
        for phase in PHASES:
            row = state["phases"][phase]
            for key in ("calls", "returned", "raised"):
                value = row[key]
                if type(value) is not int or not 0 <= value <= 64:
                    raise ValueError("H4_OBSERVER_COUNT")
                result["phases"][phase][key] = value
        rows = state["exceptions"]
        if type(rows) is not list or len(rows) > 8:
            raise ValueError("H4_OBSERVER_ROWS")
        classes = {"CompilerQAError", "ValueError", "TypeError", "RuntimeError", "AssertionError",
            "PermissionError", "FileNotFoundError", "TimeoutError", "OSError", "MemoryError", "UNKNOWN"}
        for row in rows:
            if (type(row) is not dict or row.get("phase") not in PHASES
                    or type(row.get("exception_class")) is not str or row["exception_class"] not in classes
                    or row.get("structured_code") != "UNKNOWN"):
                raise ValueError("H4_OBSERVER_EXCEPTION")
            result["exceptions"].append(dict(phase=row["phase"], exception_class=row["exception_class"],
                structured_code="UNKNOWN"))
    except BaseException:
        result = new_state()
        result["complete"] = False
    return result
