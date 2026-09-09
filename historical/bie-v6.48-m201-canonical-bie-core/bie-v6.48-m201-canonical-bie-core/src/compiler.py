from contracts import REQUIRED_STAGES
from pipeline import pipeline_run,advance
from artifact import artifact,grounded
from lineage import lineage,traceable
from config import canonical_config,compatible
from validation import validate_pipeline,complete
from observability import pipeline_event,healthy

def compile_canonical_run():
    run=pipeline_run("run-1","book://source-1",
                     canonical_config("production","provider"))
    refs={}
    for i,stage in enumerate(REQUIRED_STAGES):
        ref=f"artifact://{stage}-1"
        run=advance(run,stage,"COMPLETE",ref)
        refs[stage]=artifact(f"{stage}-1",stage,stage,ref,
                             ["book://source-1"])
    report=validate_pipeline(run)
    ev=pipeline_event("event-1","run-1","qa","SUCCESS",100)
    return {"schema_version":"6.48","run":run,
            "artifacts":refs,"config":run["options"],
            "lineage":lineage("qa-1",["render-1"],
                               ["book://source-1"]),
            "validation":report,"observability":ev,
            "quality_gate":{"valid":report["valid"] and
                                  complete(run) and
                                  grounded(refs["lesson"]) and
                                  traceable(lineage("qa-1",["render-1"],
                                  ["book://source-1"])) and
                                  compatible(run["options"]) and
                                  healthy(ev),
                            "errors":report["errors"]}}

