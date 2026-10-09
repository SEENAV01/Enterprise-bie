"""Safe M1 evidence driver. Native H3/Remotion, never global product execution.

Raw source, generated projects, measurements and media live only in a disposable
private test directory. Only the allowlisted summary below may be uploaded.
"""
import argparse
from contextlib import redirect_stdout, redirect_stderr
from dataclasses import asdict
from hashlib import sha256
import io
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tests.compiler.m1_support import prepared, admitted, TARGET, RENDER_TARGET
from bie.compiler.governed_motion import EXACT_LAYOUT, FIXTURE_LAYOUT
from bie.compiler.animation_behavior import motion_contract, motion_state, frame_window
from bie.compiler.animation_track_compiler import compile_animation_track
from bie.compiler.qa_common import digest
from bie.compiler.render_process import run_bounded_process
from tests.compiler.m1_safe_paint_diagnostics import capture_paint_diagnostic, is_safe_diagnostic
from tests.compiler.m1_safe_paint_diagnostics import observe_paint_process, is_safe_typed_observation


def require(value, code):
    if not value:
        raise ValueError("M1_PROOF_" + code)


def safe_error(exc):
    if isinstance(exc, ModuleNotFoundError) and exc.name in {"fcntl", "matplotlib", "numpy", "PIL"}:
        return {"exception_class": type(exc).__name__, "safe_code": "M1_HOST_MODULE_UNAVAILABLE",
                "missing_module": exc.name}
    code = str(exc).split(":", 1)[0]
    return {"exception_class": type(exc).__name__,
            "safe_code": code if re.fullmatch(r"[A-Z][A-Z0-9_]{1,90}", code) else "UNCLASSIFIED"}


def emitted_frames(raw, target, temporary):
    """Execute emitted TS functions for every frame, separately from rendering.

    Reuses the native explicitly-labelled hook-double bridge; its results are
    numerical/source evidence only. The independent real-render gate is required.
    """
    n = (raw["duration_ms"] * target.fps + 999) // 1000
    total = 0
    for index, track in enumerate(raw["tracks"]):
        element = next(e for e in raw["elements"] if e["element_id"] == track["element_id"])
        emitted = compile_animation_track(track, element=element)
        calls = [{"name": "evaluateTrackState", "args": [f, target.fps]} for f in range(n)]
        calls += [{"name": "evaluateTrackStyle", "args": [f, target.fps]} for f in range(n)]
        request = temporary / ("ts-" + str(index) + ".json")
        request.write_text(json.dumps({"source": emitted.source_text, "frames": [], "calls": calls}), encoding="utf-8")
        result = run_bounded_process(("node", str(ROOT / "tests/compiler/h2_jsx_test_runtime.cjs"), str(request)),
            cwd=temporary, timeout_s=45, max_output_bytes=4 * 1024**2)
        require(result.process.passed, "GENERATED_TS_EXECUTION")
        value = json.loads(result.process.stdout)
        require(value["typescript_version"] == "5.8.3" and len(value["calls"]) == 2*n, "TS_RUNTIME_IDENTITY")
        c = motion_contract(track)
        for frame in range(n):
            expected = motion_state(c, frame, target.fps)
            require(set(value["calls"][frame]) == set(expected) and all(
                abs(value["calls"][frame][k] - v) <= 1e-12 for k, v in expected.items()), "FRAME_PARITY")
            style = {"opacity": expected["opacity"]} if "opacity" in expected else {}
            require(value["calls"][n+frame] == style, "STYLE_PARITY")
        total += n
    return {"frame_track_states_checked": total, "python_emitted_ts_agree": True,
            "bridge_scope": "EXPLICIT_HOOK_DOUBLES_NOT_RENDER_PROOF", "typescript": "5.8.3"}


def decoded_frames(capture, raw, target):
    """Decode every full native frame; preserve content/geometry and motion order.

    Native paint/fit/raster validators independently inspect every frame and
    counterfactual image first. This adds action-specific conservation assertions.
    """
    import numpy as np
    from bie.compiler.raster_ink import read_png, RasterPolicy
    data = json.loads((capture / "RESULT.json").read_text(encoding="utf-8"))
    n = (raw["duration_ms"] * target.fps + 999) // 1000
    require(len(data["frames"]) == n and data["browser_errors"] == [], "CAPTURE_COMPLETENESS")
    tracks = {t["element_id"]: motion_contract(t) for t in raw["tracks"]}
    elements = {e["element_id"]: e for e in raw["elements"]}
    baseline = read_png(capture / data["frames"][0]["image"],
        expected_sha256=data["frames"][0]["image_sha256"], size=(target.width, target.height))
    final = read_png(capture / data["frames"][-1]["image"],
        expected_sha256=data["frames"][-1]["image_sha256"], size=(target.width, target.height))
    final_rows = {r["element_id"]: r for r in data["frames"][-1]["measurement"]["records"]}
    final_paint = {r["element_id"]: r for r in data["frames"][-1]["measurement"]["paint_records"]}
    boxes = {}
    for eid, e in elements.items():
        b = e["normalized_box"]
        boxes[eid] = tuple(int(round(v)) for v in (b["x"]*target.width, b["y"]*target.height,
                                                  b["width"]*target.width, b["height"]*target.height))
    # A conservative one-pixel border covers anti-aliasing only, not motion.
    def mask_box(mask, box, pad=1):
        x,y,w,h = box
        x0,y0=max(0,int(x)-pad),max(0,int(y)-pad)
        x1,y1=min(target.width,int(np.ceil(x+w))+pad),min(target.height,int(np.ceil(y+h))+pad)
        mask[y0:y1,x0:x1] = True
    masks = {}
    for eid, c in tracks.items():
        mask = np.zeros((target.height, target.width), dtype=bool)
        if c.parameters["binding"]["element_type"] == "chart":
            # Exact canonical bar emitter order: two static axes, then one
            # data-value rect per source value. Labels are separate text records.
            ink = final_paint[eid]["ink"]
            expected = len(elements[eid]["props"]["values"])
            require(len(ink) == expected + 2, "NATIVE_BAR_INVENTORY")
            for shape in ink[2:]: mask_box(mask, shape["box"])
        else:
            mask_box(mask, boxes[eid])
        masks[eid] = mask
    allowed = np.logical_or.reduce(list(masks.values()))
    visible_focus, reveals = {k: 0 for k,c in tracks.items() if c.action == "emphasize"}, {}
    stable = {}
    schedule = sha256()
    for frame, record in enumerate(data["frames"]):
        require(record["frame"] == frame, "FRAME_ORDER")
        image = read_png(capture / record["image"], expected_sha256=record["image_sha256"], size=(target.width,target.height))
        require(np.array_equal(image[~allowed], baseline[~allowed]), "STATIC_CONTEXT_CHANGED")
        rows = {r["element_id"]: r for r in record["measurement"]["records"]}
        for eid, c in tracks.items():
            row = rows[eid]
            require(row["layer_box"] == final_rows[eid]["layer_box"], "TARGET_GEOMETRY_CHANGED")
            state = motion_state(c,frame,target.fps)
            schedule.update(json.dumps({"frame": frame, "target": eid, "state": state}, sort_keys=True).encode())
            if c.action == "emphasize":
                require(row["rendered_text"] == final_rows[eid]["rendered_text"], "FOCUS_CONTENT_CHANGED")
                x,y,w,h = boxes[eid]
                require(np.array_equal(image[y+8:y+h-8,x+8:x+w-8], baseline[y+8:y+h-8,x+8:x+w-8]), "FOCUS_INNER_CONTENT_CHANGED")
                delta = np.max(np.abs(image[masks[eid]].astype(int)-baseline[masks[eid]].astype(int)))
                if state["focus_opacity"] == 0:
                    require(delta == 0, "FOCUS_OUTSIDE_WINDOW")
                if state["focus_opacity"] >= .8:
                    require(delta >= RasterPolicy().pixel_delta, "FOCUS_NO_VISIBLE_CHANGE")
                    visible_focus[eid] += 1
            else:
                alpha = state.get("opacity", state.get("series_opacity"))
                expected = final if alpha == 1 else baseline
                require(np.array_equal(image[masks[eid]],expected[masks[eid]]), "REVEAL_VALUE_OR_ORDER_CHANGED")
                if alpha == 1:
                    reveals.setdefault(eid, frame)
                    require(np.any(final[masks[eid]] != baseline[masks[eid]]), "REVEAL_NO_VISIBLE_CHANGE")
                if "series_opacity" in state:
                    require(row["rendered_text"] == final_rows[eid]["rendered_text"], "CHART_STATIC_LABELS_CHANGED")
                elif alpha == 1:
                    require(row["rendered_text"] == final_rows[eid]["rendered_text"], "REVEAL_CONTENT_CHANGED")
            if row["visible"]:
                layout_identity = digest({"layer": row["layer_box"], "text": row["rendered_text"], "text_boxes": row["text_boxes"]})
                require(stable.setdefault(eid,layout_identity) == layout_identity, "VISIBLE_LAYOUT_CHANGED")
    require(all(count > 0 for count in visible_focus.values()), "FOCUS_NOT_OBSERVED")
    ordered = sorted((c.start_ms, eid) for eid,c in tracks.items() if c.action == "reveal")
    require([reveals[eid] for _,eid in ordered] == sorted(reveals.values()), "REVEAL_SEQUENCE_CHANGED")
    return {"frames_decoded": n, "complete_schedule_checked": True, "geometry_content_conserved": True,
            "focus_targets_visible": len(visible_focus), "reveals_observed": len(reveals),
            "schedule_sha256": schedule.hexdigest(), "learning_equivalence": "NOT_EVALUATED", "accepted": False}


def run(args):
    result = {"schema": "bie.task036.m1-proof/1", "platform": platform.system(),
        "python": platform.python_version(), "mode": args.mode, "cases": [], "passed": False,
        "product_accepted": False, "global_scene_ir_executed": False,
        "global_video_code_compile_render_executed": False, "native_test_render_executed": False}
    fixture = None
    try:
        from bie.compiler.hardened_scene_compile import compile_h3_scene, publish_h3_scene
        families = (args.family,) if args.family else ("quantitative", "chronology", "cellular", "cellular_reduced")
        fixture,cases = prepared(families)
        for family,run_id in cases.items():
            presentation = EXACT_LAYOUT if args.mode == "source" else FIXTURE_LAYOUT
            target = TARGET if args.mode == "source" else RENDER_TARGET
            with admitted(fixture,run_id,presentation=presentation) as (raw,bound,_), tempfile.TemporaryDirectory(prefix="bie-m1-private-") as temp:
                root = Path(temp)
                row = {"family": family, "presentation": presentation, "native_pdf_upstream": True,
                    "global_stages": 10, "upstream_admission_sha256": bound["identity"],
                    "tracks": len(raw["tracks"]), "source_fields": sorted({k for t in raw["tracks"] for k in t["parameters"]["mapping"]}),
                    "preferences": [], "passed": False}
                result["cases"].append(row)
                for preference in ((args.preference,) if args.preference else ("standard","reduced")):
                    phase = {"preference": preference, "h3_passed": False, "render_passed": False}
                    row["preferences"].append(phase)
                    phase["phase"] = "H3_SOURCE"
                    compiled = compile_h3_scene(raw,target=target,motion_preference=preference)
                    phase["source_codes"] = sorted({f.code for f in compiled.receipt.findings if f.severity == "ERROR"})
                    require(compiled.receipt.source_gate_passed, "H3_SOURCE_BLOCKED")
                    phase.update(h3_passed=True, layer_frames=compiled.layout["frames_evaluated"],
                        manifest_sha256=compiled.receipt.manifest_sha256, motion_sha256=digest(compiled.motion),
                        host_identity=compiled.host["identity_sha256"])
                    phase["phase"] = "EMITTED_NUMERIC_SCHEDULE"
                    phase["emitted"] = emitted_frames(raw,target,root)
                    if args.mode == "render":
                        from bie.compiler.real_paint import produce_actual_paint, require_actual_witness
                        project = root / ("project-" + preference)
                        phase["phase"] = "H3_TEST_PUBLICATION"
                        receipt = publish_h3_scene(raw,project,target=target,motion_preference=preference)
                        process = run_bounded_process(("npm","install","--ignore-scripts","--no-audit","--no-fund","--fetch-retries=0","--fetch-timeout=15000"),
                            cwd=project,timeout_s=180,max_output_bytes=4*1024**2)
                        require(process.process.passed,"NPM_SETUP")
                        output = root / ("paint-" + preference)
                        phase["phase"] = "REAL_GENERATED_CONSUMER"
                        with observe_paint_process() as typed_observer:
                            try:
                                witness = produce_actual_paint(project,output,node=shutil.which("node"),browser=args.browser,target=target)
                            except Exception:
                                # Snapshot only fixed private receipt fields BEFORE
                                # TemporaryDirectory cleanup. Evidence cannot mask
                                # or downgrade the original fail-closed rejection.
                                try:
                                    diagnostic = capture_paint_diagnostic(root, family=family, preference=preference,
                                        frame_count=phase["layer_frames"], duration_ms=raw["duration_ms"], fps=target.fps)
                                    if is_safe_diagnostic(diagnostic):
                                        phase["paint_process_diagnostic"] = diagnostic
                                except Exception:
                                    pass
                                try:
                                    typed = typed_observer.snapshot()
                                    if is_safe_typed_observation(typed):
                                        phase["paint_process_typed_observation"] = typed
                                except BaseException:
                                    pass
                                raise
                        phase["native_qa"] = {name: {"passed": witness.evidence[name]["passed"],
                            "codes": sorted({f["code"] for f in witness.evidence[name]["findings"]})}
                            for name in ("fit", "paint", "raster")}
                        require_actual_witness(witness,receipt.manifest_sha256)
                        phase["phase"] = "DECODED_FRAME_CONSERVATION"
                        phase["decoded"] = decoded_frames(output / "capture",raw,target)
                        phase.update(render_passed=True, render_evidence_sha256=witness.evidence_sha256,
                            frame_count=witness.frame_count, fit_passed=witness.evidence["fit"]["passed"],
                            paint_passed=witness.evidence["paint"]["passed"], raster_passed=witness.evidence["raster"]["passed"])
                        result["native_test_render_executed"] = True
                    phase["phase"] = "COMPLETE"
                row["passed"] = True
        result["passed"] = bool(result["cases"]) and all(r["passed"] for r in result["cases"])
    except Exception as exc:
        result["failure"] = safe_error(exc)
    finally:
        if fixture is not None: fixture.tearDown()
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=("source","render"),required=True)
    p.add_argument("--family",choices=("quantitative","chronology","cellular","cellular_reduced"))
    p.add_argument("--preference",choices=("standard","reduced"))
    p.add_argument("--browser")
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    # Private captures are never forwarded, including on failure.
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()): result=run(args)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"passed":result["passed"],"mode":args.mode,"failure":result.get("failure"),"product_accepted":False}))
    return 0 if result["passed"] else 1


if __name__ == "__main__": raise SystemExit(main())
