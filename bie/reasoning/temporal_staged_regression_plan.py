"""RE-TEMP-058 — Define mandatory regression stages for safe Temporal integration."""
from dataclasses import dataclass

@dataclass(frozen=True)
class RegressionStage:
    name: str
    required: bool = True

MANDATORY_STAGES = (
    RegressionStage("atomic_task_tests"),
    RegressionStage("temporal_section_tests"),
    RegressionStage("reasoning_section_tests"),
    RegressionStage("enterprise_runner"),
    RegressionStage("import_smoke"),
)

def evaluate_regression_results(results):
    missing=[]
    failed=[]
    for stage in MANDATORY_STAGES:
        if stage.name not in results:
            missing.append(stage.name)
        elif results[stage.name] is not True:
            failed.append(stage.name)
    if missing:
        return {"ready":False,"status":"MISSING_STAGE","details":tuple(missing)}
    if failed:
        return {"ready":False,"status":"FAILED_STAGE","details":tuple(failed)}
    return {"ready":True,"status":"PASS","details":()}
