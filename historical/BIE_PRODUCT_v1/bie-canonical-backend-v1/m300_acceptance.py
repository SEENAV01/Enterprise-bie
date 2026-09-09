from pathlib import Path

REQUIRED_ARTIFACTS = (
    "source", "knowledge", "teaching_plan", "script",
    "scene_dsl", "remotion_project", "mp4", "qa_report"
)

def artifact_ok(value):
    if value is None:
        return False
    if isinstance(value, (str, Path)):
        # M300 receives artifact references from a manifest. A non-empty
        # reference is present even when the referenced path is virtual in a
        # contract test; physical-file validation belongs to the producing gate.
        return bool(str(value).strip())
    return True

def validate_artifact_set(artifacts):
    missing=[k for k in REQUIRED_ARTIFACTS if not artifact_ok(artifacts.get(k))]
    return {"passed":not missing,"missing":missing}

def acceptance_gate(artifacts, qa_result):
    artifact_report=validate_artifact_set(artifacts)
    qa_passed=qa_result.get("status")=="accepted"
    return {
        "accepted": artifact_report["passed"] and qa_passed,
        "artifact_validation":artifact_report,
        "qa_result":qa_result,
        "reason": "ACCEPTED" if artifact_report["passed"] and qa_passed
                  else ("MISSING_ARTIFACTS" if not artifact_report["passed"]
                        else "QA_NOT_ACCEPTED")
    }

def build_acceptance_record(lesson_id, artifacts, qa_result):
    gate=acceptance_gate(artifacts,qa_result)
    return {
        "milestone":"M300",
        "lesson_id":lesson_id,
        "accepted":gate["accepted"],
        "gate":gate,
        "artifact_manifest":{k:str(v) for k,v in artifacts.items()}
    }
