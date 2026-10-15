"""Bounded diagnostic for the two observed Task036 failures; no gate waiver.

Uses unchanged native code, budgets and original test ordering. Private exception
text is inspected transiently ONLY for literal closed-category matching and is
never stored, formatted, logged or exported. No argv, paths, media or tokens are
included in receipts. This is not source review or product acceptance.
"""
import argparse
from contextlib import contextmanager
import json
from pathlib import Path
import resource
import runpy
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def write(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(row, sort_keys=True, indent=2) + "\n")


def error_label(exc):
    from bie.compiler.qa_common import CompilerQAError
    from playwright.sync_api import Error, TimeoutError as PWTimeout
    types = ((CompilerQAError, "COMPILER_QA"), (PWTimeout, "PLAYWRIGHT_TIMEOUT"),
        (Error, "PLAYWRIGHT_ERROR"), (PermissionError, "PERMISSION"),
        (FileNotFoundError, "NOT_FOUND"), (TimeoutError, "TIMEOUT"),
        (ValueError, "VALUE"), (OSError, "OS"))
    label = next((label for cls, label in types if type(exc) is cls), "OTHER")
    code = "UNCLASSIFIED"
    # Exact trusted exception classes only; do not invoke foreign properties,
    # __str__, repr, traceback formatting or a caller's arbitrary conversion.
    if type(exc) is CompilerQAError:
        args = BaseException.args.__get__(exc)
        value = args[0] if type(args) is tuple and len(args) == 1 else None
        known = {"LAYOUT_BROWSER_UNAVAILABLE", "LAYOUT_BROWSER_TIMEOUT_INVALID",
            "LAYOUT_BROWSER_NOT_STARTED", "LAYOUT_BRIDGE_FAILED",
            "LAYOUT_BRIDGE_SCOPE_MISMATCH", "LAYOUT_BRIDGE_COVERAGE_MISMATCH",
            "LAYOUT_EVIDENCE_ALREADY_EXISTS", "HOST_TOOLCHAIN_UNAVAILABLE",
            "TYPESCRIPT_PARSER_UNAVAILABLE", "TOOLCHAIN_CHANGED_DURING_HASH"}
        if type(value) is str and len(value) <= 16384:
            prefix = value.partition(":")[0]
            code = prefix if prefix in known else "UNCLASSIFIED"
    elif type(exc) in (Error, PWTimeout):
        value = exc.message  # Trusted pinned Playwright implementation.
        if type(value) is str and len(value) <= 16384:
            lower = value.lower()
            matches = (
                ("executable doesn't exist", "EXECUTABLE_ABSENT"),
                ("missing dependencies", "SHARED_DEPENDENCIES_MISSING"),
                ("sync api inside the asyncio loop", "SYNC_API_IN_ASYNC_LOOP"),
                ("target page, context or browser has been closed", "BROWSER_TARGET_CLOSED"),
                ("connection closed while reading", "DRIVER_CONNECTION_CLOSED"),
                ("failed to launch", "BROWSER_LAUNCH_FAILED"),
                ("timeout", "PLAYWRIGHT_TIMEOUT_MESSAGE"),
            )
            code = next((code for literal, code in matches if literal in lower), "UNCLASSIFIED")
    return dict(exception_class=label, code=code)


@contextmanager
def layout_observation():
    from bie.compiler import layout_browser, layout_repair
    functions = {
        layout_browser.ChromiumLayoutProbe.__init__: "BROWSER_CONSTRUCTOR",
        layout_browser.ChromiumLayoutProbe.__enter__: "BROWSER_ENTER",
        layout_browser.ChromiumLayoutProbe.__exit__: "BROWSER_EXIT",
        layout_browser.ChromiumLayoutProbe.measure: "MEASURE",
        layout_repair.repair_scene_layout: "REPAIR",
        layout_repair._run_candidates: "CANDIDATES",
    }
    bindings = {f.__code__: (f.__globals__, label) for f, label in functions.items()}
    output = dict(schema="bie.task036.layout-boundary-cause/1", availability="UNAVAILABLE",
        events=[], event_limit_reached=False, accepted=False, product_accepted=False)
    previous = sys.gettrace()
    if previous is not None:
        output["reason"] = "EXISTING_TRACE"
        yield output
        return

    def trace(frame, event, arg):
        binding = bindings.get(frame.f_code)
        if binding is None or frame.f_globals is not binding[0]:
            return None
        if event == "exception":
            if len(output["events"]) < 16:
                try:
                    row = dict(site=binding[1], **error_label(arg[1]))
                    output["events"].append(row)
                except BaseException:
                    output["events"].append(dict(site=binding[1], exception_class="UNKNOWN", code="OBSERVATION_FAILED"))
            else:
                output["event_limit_reached"] = True
        return trace
    output["availability"] = "VALID"
    sys.settrace(trace)
    try:
        yield output
    finally:
        sys.settrace(previous)


def native(args):
    from tests.compiler import run_m1_tests as runner
    original = runner.run_file
    def observed(path, identities, root=runner.ROOT):
        if path != "tests/compiler/test_comp_h4_005.py":
            return original(path, identities, root)
        with layout_observation() as receipt:
            result = original(path, identities, root)
        # Full unchanged collection, assertions, ordering and result decide PASS.
        write(args.output.parent / "h4-boundary.json", dict(test_file=path,
            selected=result["selected"], executed=result["executed"], passed=result["passed"],
            observation=receipt, diagnostic_only=True, product_accepted=False))
        return result
    runner.run_file = observed
    previous = sys.argv
    sys.argv = [str(ROOT / "tests/compiler/run_m1_tests.py"), "--lane", "native-extra", "--output", str(args.output)]
    try:
        return runner.main()
    finally:
        sys.argv = previous
        runner.run_file = original


def child(args):
    from tests.productization.scene_ir.positive_process_observations import Checkpoints
    original = Checkpoints.mark
    def mark(self, phase, stage="UNKNOWN", index=0, boundary="UNKNOWN"):
        original(self, phase, stage, index, boundary)
        if phase == "NATIVE_BOUNDARY" and stage == "SCENE_IR" and boundary == "before_next_admission":
            write(args.output.parent / "tail-start.json", dict(process_cpu_s=time.process_time(),
                cpu_limits=resource.getrlimit(resource.RLIMIT_CPU), accepted=False, product_accepted=False))
    Checkpoints.mark = mark
    prior = sys.argv
    sys.argv = [str(ROOT / "apps/operator/scene_ir_worker_child.py"), *args.worker_args]
    try:
        runpy.run_path(sys.argv[0], run_name="__main__")
    finally:
        write(args.output.parent / "tail-end.json", dict(process_cpu_s=time.process_time(),
            accepted=False, product_accepted=False))
        Checkpoints.mark = original
        sys.argv = prior


def scene(args):
    from apps.operator import process_supervision as supervisor
    from scripts.smoke_bie_scene_ir import journey, run_smoke, SmokeFailure
    original = supervisor.supervise
    children = []
    def measured(command, env, budget, data=None):
        # Preserve -I/-B, original worker and every original process budget.
        child_output = args.output.parent / ("child-%02d" % (len(children) + 1)) / "boundary.json"
        invoke = (command if "--verify-only" in command else command[:3] +
            [str(Path(__file__).resolve()), "--mode", "child", "--output", str(child_output), "--"] + command[4:])
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        started = time.monotonic()
        result = original(invoke, env, budget, data)
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        row = dict(mode="VERIFY" if "--verify-only" in command else "RUN",
            completed=result.completed, exit_code=result.exit_code,
            wall_s=time.monotonic()-started, user_cpu_s=after.ru_utime-before.ru_utime,
            system_cpu_s=after.ru_stime-before.ru_stime, output_bytes=len(result.output),
            children_maxrss_kib=after.ru_maxrss, diagnostic_only=True, product_accepted=False)
        children.append(row)
        write(args.output.parent / "child-accounting.json", children)
        return result
    supervisor.supervise = measured
    try:
        if args.mode == "scene-full":
            output = run_smoke()
        else:
            result = journey(("Chart B x A y B: C 2; D 3.",), "NOT_REQUIRED")
            output = dict(passed=result["passed"], children=children,
                second_process_restart=result["second_process_restart"],
                idempotent_replay=result["idempotent_replay"], product_accepted=False)
    except SmokeFailure as error:
        output = dict(passed=False, code=error.code, diagnostics=error.diagnostics, product_accepted=False)
    except Exception:
        output = dict(passed=False, code="scene_ir_smoke_failed", product_accepted=False)
    finally:
        supervisor.supervise = original
    if args.mode != "scene-full":
        output.update(diagnostic_only=True, source_commit_role="CURRENT_CHECKOUT_NOT_A_PRODUCT_APPROVAL")
    write(args.output, output)
    print(json.dumps(output, sort_keys=True))
    return 0 if output["passed"] else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("scene", "scene-full", "native", "child"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("worker_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.worker_args[:1] == ["--"]:
        args.worker_args = args.worker_args[1:]
    if args.mode == "child": return child(args)
    return scene(args) if args.mode in ("scene", "scene-full") else native(args)


if __name__ == "__main__":
    raise SystemExit(main())
