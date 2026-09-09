from failure import failure,valid as failure_valid
from diagnosis import diagnosis,valid as diagnosis_valid
from remediation import remediation,valid as remediation_valid
from impact import impact_analysis,minimal_scope
from regeneration import regeneration_job,valid as regeneration_valid
from reqa import reqa_cycle,passed as cycle_passed
from guard import regeneration_guard,safe
from provenance import provenance,traceable
from verification import verification,passed

def build_remediation_loop():
    f=failure("fail-1","VISUAL","MEDIUM","asset-force-diagram",
              "qa-scene-coverage","Diagram does not match scene requirement.",
              "wrong-arrow-direction","correct-force-direction")

    d=diagnosis("diag-1",f["failure_id"],
                "Visual asset specification mismatch",
                ["asset-force-diagram"],0.96,
                "QA failure maps directly to the affected visual asset.")

    r=remediation(
        "rem-1","REGENERATE_ASSET",["asset-force-diagram"],
        "Regenerate only the failed visual asset.",
        ["asset-force-equation","audio-1"],
        {"preserve_scene_timing":True}
    )

    impact=impact_analysis(
        "impact-1",[f["target_ref"]],
        ["asset-force-equation","audio-1"],
        ["sc3"],["scene:sc3","asset:asset-force-diagram"]
    )

    job=regeneration_job(
        "regen-1",r["action_id"],r["target_refs"],
        ["spec-1","prompt-1"],1
    )

    cycle=reqa_cycle(
        "cycle-1",job["job_id"],"report-2","PASS",
        ["asset-force-diagram"]
    )

    guard=regeneration_guard(
        [f["failure_id"]],[r["action_id"]],
        ["asset-force-equation","audio-1"],3
    )

    prov=provenance(
        "loop-1",["job-1","regen-1"],[f["failure_id"]],
        [d["diagnosis_id"]],[r["action_id"]],["report-2"],
        ["artifact://render-qa"]
    )

    check=verification(
        "verify-remediation","loop-1","PASS"
    )

    return {
        "schema_version":"6.59",
        "failure":f,
        "diagnosis":d,
        "remediation":r,
        "impact_analysis":impact,
        "regeneration_job":job,
        "reqa_cycle":cycle,
        "regeneration_guard":guard,
        "provenance":prov,
        "verification":check,
        "quality_gate":{"valid":(
            failure_valid(f) and diagnosis_valid(d)
            and remediation_valid(r) and minimal_scope(impact)
            and regeneration_valid(job) and cycle_passed(cycle)
            and safe(guard) and traceable(prov) and passed(check)
        ),"errors":[]}
    }
