import re
from pathlib import Path

MATH_HINTS = re.compile(
    r"(=|≠|≤|≥|→|←|∑|√|∫|π|\^|_|\bfrac\b|\bsqrt\b|[A-Za-z]\s*=\s*[A-Za-z0-9])"
)

def classify_text(text):
    if not text:
        return "unknown"
    return "equation_candidate" if MATH_HINTS.search(text) else "text"

def extract_equation_candidates(ocr_report):
    candidates=[]
    for frame in ocr_report.get("checks", []):
        # M292 preserves word counts but not full line geometry in its report.
        # This layer therefore only flags OCR text as a candidate; it does not
        # pretend to reconstruct an equation that the upstream artifact did not preserve.
        if frame.get("word_count",0) > 0:
            candidates.append({
                "frame":frame["frame"],
                "classification":"equation_candidate_possible",
                "source":"ocr_text_qa"
            })
    return candidates

def inspect_scene_visual_primitives(scene_dsl):
    findings=[]
    for scene in scene_dsl.get("scenes",[]):
        visuals=scene.get("visuals",[])
        types=[v.get("type") for v in visuals]
        findings.append({
            "scene_id":scene.get("scene_id"),
            "has_title":"title" in types,
            "has_source_text":"source_text" in types,
            "diagram_count":sum(t=="diagram" for t in types),
            "equation_count":sum(t=="equation" for t in types)
        })
    return findings

def build_equation_diagram_report(scene_dsl, ocr_report):
    findings=inspect_scene_visual_primitives(scene_dsl)
    candidates=extract_equation_candidates(ocr_report)
    errors=[]
    # Missing explicit equation/diagram primitives are not failures: they are
    # actionable gaps when the source/lesson requires them.
    return {
        "passed":not errors,
        "errors":errors,
        "scene_visual_findings":findings,
        "ocr_equation_candidates":candidates,
        "semantic_status":"not_proven",
        "notes":[
            "Equation correctness is not established by OCR alone.",
            "Diagram correctness is not established by presence of a diagram primitive.",
            "Expected equation/diagram requirements need to come from the teaching/script artifacts."
        ]
    }

def generate_equation_diagram_repair_plan(report):
    repairs=[]
    if report.get("ocr_equation_candidates"):
        repairs.append({
            "action":"compare_equation_against_source",
            "reason":"ocr_equation_candidate_detected"
        })
    for scene in report.get("scene_visual_findings",[]):
        if scene.get("equation_count",0) or scene.get("diagram_count",0):
            repairs.append({
                "action":"semantic_visual_review",
                "scene_id":scene.get("scene_id"),
                "reason":"equation_or_diagram_primitive_present"
            })
    return {
        "version":"1.0",
        "repairs":repairs,
        "automatic_repairs_applied":False
    }

def validate_equation_diagram_report(report):
    errors=[]
    if "semantic_status" not in report:
        errors.append("missing_semantic_status")
    if not isinstance(report.get("scene_visual_findings"),list):
        errors.append("invalid_scene_visual_findings")
    return {"passed":not errors,"errors":errors}
