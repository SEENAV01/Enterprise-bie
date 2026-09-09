from pathlib import Path
import json
from semantic_verify_repair import apply_safe_repairs, hash_dsl
from mp4_renderer import render_mp4, validate_render

def apply_repair_and_prepare(scene_dsl, semantic_report):
    patch = semantic_report.get("repair_patch", {})
    repaired, changed = apply_safe_repairs(scene_dsl, patch)
    return {
        "changed": changed,
        "source_hash_before": hash_dsl(scene_dsl),
        "source_hash_after": hash_dsl(repaired),
        "scene_dsl": repaired,
        "patch": patch
    }

def regression_compare(before_report, after_report):
    before = before_report.get("semantic_visual_qa", {})
    after = after_report.get("semantic_visual_qa", {})
    before_m = before.get("mismatch_count", 0)
    after_m = after.get("mismatch_count", 0)
    return {
        "passed": after_m <= before_m,
        "mismatches_before": before_m,
        "mismatches_after": after_m,
        "improved": after_m < before_m,
        "reason": "no_regression" if after_m <= before_m else "regression_detected"
    }

def execute_repair_cycle(scene_dsl, semantic_report, project_meta, output_dir):
    prep = apply_repair_and_prepare(scene_dsl, semantic_report)
    if prep["changed"] == 0:
        return {
            "status":"no_change_required",
            "changed":0,
            "scene_dsl":scene_dsl,
            "render":None,
            "regression":None
        }
    repaired_meta = dict(project_meta)
    # Caller is responsible for regenerating the Remotion project from repaired DSL.
    return {
        "status":"repair_prepared",
        "changed":prep["changed"],
        "source_hash_before":prep["source_hash_before"],
        "source_hash_after":prep["source_hash_after"],
        "scene_dsl":prep["scene_dsl"],
        "patch":prep["patch"]
    }
