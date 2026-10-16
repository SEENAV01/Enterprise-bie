"""Declared compiler test catalogs, NOT a Task036 production Scene IR producer.

Upstream motion is actually produced from native PDFs by unchanged Task035.
The small diagnostic catalog exists only to exercise the native consumer. No
global scene.ir or downstream stage is committed by this helper.
"""
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import replace
import importlib.util
from pathlib import Path
import sys
from tests.compiler.h3_test_support import TARGET as NATIVE_TARGET, scene
from bie.compiler.producer_motion_admission import current_motion_admission
from bie.compiler.governed_motion import METADATA, EXACT_LAYOUT, FIXTURE_LAYOUT
TARGET = replace(NATIVE_TARGET, width=1280, height=720)
RENDER_TARGET = replace(NATIVE_TARGET, width=960, height=640)

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("m1_original_animation_tests",
    ROOT / "tests/productization/animation/test_animation_producer.py")
upstream = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upstream)


def prepared(families=("quantitative", "chronology", "cellular", "cellular_reduced")):
    f = upstream.AnimationFixture()
    f.setUp()
    cases = {}
    for family in families:
        if family == "quantitative": cases[family] = f.run
        elif family in {"chronology", "cellular", "cellular_reduced"}:
            lines = (upstream.TIMELINE,) if family == "chronology" else (upstream.CELL,)
            cases[family] = f.admit_other(lines, "m1-" + family,
                cfg=upstream.config(f.stack, reduced=family.endswith("_reduced")))
        else: raise ValueError("M1_UNKNOWN_FIXTURE")
    try:
        for run in cases.values():
            result = f.complete(run)
            if result.get("slice_complete") is not True:
                raise AssertionError("M1_UPSTREAM_FIXTURE_INCOMPLETE")
        return f, cases
    except BaseException:
        f.tearDown()
        raise


def catalog(service, run, tenant, *, presentation=EXACT_LAYOUT):
    plan, receipt = service.verified_animation(run, tenant)
    current = service.read(run, receipt["current_inputs_id"])
    handoff = service.read(run, receipt["handoff_id"])
    targets = {pid for n in handoff["nodes"] for pid in n["target_ids"]}
    elements = []
    for row in current["rows"]:
        items = {x["id"]: x for x in row["semantic_obligations"]["source_items"]}
        for p in row["primitive_rows"]:
            if p["primitive_id"] not in targets:
                continue
            selected = [items[i] for i in p["source_item_ids"]]
            if row["semantic_kind"] == "sampled_chart":
                kind = "chart"
                props = {"chart_kind": "bar", "categories": [x["label"] for x in selected],
                    "values": [x["value"] for x in selected]}
                for key in ("x_label", "y_label", "units"):
                    props[key] = row["semantic_obligations"]["axis"][key] if key != "units" else ""
            else:
                kind = "diagram"
                item = selected[0]
                label = item["label"]
                if row["semantic_kind"] == "timeline":
                    label += " | " + item["time_label"] + (" | uncertain" if item["uncertain"] else "")
                # Versioned TEST presentation geometry; no biological size or
                # elapsed-time claim. Final source-derived catalog is NOT here.
                props = {"diagram_kind": "m1-technical-item", "view_box": [0, 0, 240, 100],
                    "nodes": [{"node_id": item["id"], "label": label, "x": 40, "y": 25,
                        "width": 160, "height": 50, "font_size": 16}], "edges": []}
            box = ({"x": .05, "y": .05, "width": .9, "height": .9}
                if presentation == FIXTURE_LAYOUT and kind == "chart" else deepcopy(p["layout"]["box"]))
            elements.append({"element_id": p["primitive_id"], "element_type": kind, "props": props,
                "normalized_box": box,
                "accessibility": {"alt": "Synthetic compiler contract fixture",
                    "color_independent_encoding": True,
                    "reduced_motion_variant": "m1:" + p["primitive_id"]},
                "source_refs": list(p["source_refs"]), "reasoning_refs": list(p["reasoning_refs"])})
    return elements


@contextmanager
def admitted(fixture, run, *, presentation=EXACT_LAYOUT):
    with fixture.port.native(fixture.p, run, "read") as service:
        elements = catalog(service, run, fixture.p.tenant, presentation=presentation)
        with current_motion_admission(service, run, fixture.p.tenant, elements, presentation=presentation) as bound:
            raw = scene()
            raw["scene_id"] = bound["scene_id"]
            raw["duration_ms"] = bound["duration_ms"]
            raw["elements"] = elements
            raw["tracks"] = list(bound["tracks"].values())
            raw["source_refs"] = list(bound["upstream"]["plan"]["source_refs"])
            raw["reasoning_refs"] = list(bound["upstream"]["plan"]["reasoning_refs"])
            raw["metadata"] = {"fixture": "M1_COMPILER_ONLY_NOT_TASK036_CATALOG", METADATA: bound["metadata"],
                "compiler_h3": {"reduced_motion_variants": {}}}
            registry = raw["metadata"]["compiler_h3"]["reduced_motion_variants"]
            for e in elements:
                registry[e["accessibility"]["reduced_motion_variant"]] = {
                    "element_id": e["element_id"], "reason": "Explicit non-geometric source-bound M1 technical variant; learning equivalence not evaluated",
                    "source_refs": list(e["source_refs"]), "reasoning_refs": list(e["reasoning_refs"]),
                    "track_replacements": {t["track_id"]: {"action": t["action"], "parameters": deepcopy(t["parameters"])}
                        for t in raw["tracks"] if t["element_id"] == e["element_id"]}}
            raw["capability_requests"] = [{"capability_id": "comp:m1:" + e["element_type"],
                "element_id": e["element_id"], "element_type": e["element_type"],
                "requested_action": t["action"], "required": True}
                for e in elements for t in raw["tracks"] if t["element_id"] == e["element_id"]]
            yield raw, bound, service
