from lesson_job import lesson_job,valid as job_valid
from orchestrator import LessonOrchestrator
from state_event import state_event,valid as event_valid
from artifact_registry import artifact,registry,valid as artifact_valid
from stage_contract import satisfied
from checkpoint import checkpoint,resumable
from failure_policy import failure_policy,should_fail
from provenance import provenance,traceable
from verification import verification,passed

def build_end_to_end_orchestrator():
    job=lesson_job(
        "lesson-job-1","source://physics-lesson-1",
        "output://lesson-1.mp4"
    )
    orch=LessonOrchestrator(job)
    orch.run_happy_path()

    artifacts=[
        artifact("a-understanding","understanding","artifact://understanding",
                  "UNDERSTOOD"),
        artifact("a-plan","plan","artifact://plan","PLANNED"),
        artifact("a-script","script","artifact://script","SCRIPTED"),
        artifact("a-storyboard","storyboard","artifact://storyboard","STORYBOARDED"),
        artifact("a-assets","asset_manifest","artifact://assets","ASSETS_READY"),
        artifact("a-audio","audio_plan","artifact://audio","AUDIO_READY"),
        artifact("a-composition","composition","artifact://composition","COMPOSED"),
        artifact("a-video","rendered_video","output://lesson-1.mp4","RENDERED"),
        artifact("a-qa","quality_report","artifact://qa-report","QA_EVALUATED"),
        artifact("a-verification","verification","artifact://verification","VERIFIED")
    ]
    reg=registry(artifacts)

    events=[]
    for i,e in enumerate(orch.events,1):
        events.append(state_event(
            f"event-{i}",job["job_id"],e["from_state"],e["to_state"],
            e["reason"],e["artifact_refs"],e["evidence_refs"]
        ))

    cp=checkpoint("checkpoint-final",job["job_id"],job["state"],
                  [a["artifact_id"] for a in artifacts],len(events))
    policy=failure_policy(3,True)

    v=verification(
        "verify-lesson",job["job_id"],job["state"],"PASS",
        ["artifact://qa-report","artifact://verification"],
        "output://lesson-1.mp4"
    )
    prov=provenance(
        job["job_id"],[job["source_ref"]],
        [f"event-{i}" for i in range(1,len(events)+1)],
        [a["artifact_id"] for a in artifacts],
        [cp["checkpoint_id"]]
    )

    return {
        "schema_version":"6.61",
        "lesson_job":job,
        "state_machine":{"states":orch.events,
                         "current_state":orch.state},
        "state_events":events,
        "artifact_registry":reg,
        "checkpoints":[cp],
        "failure_policy":policy,
        "verification":v,
        "provenance":prov,
        "quality_gate":{"valid":(
            job_valid(job)
            and orch.state=="VERIFIED"
            and all(event_valid(e) for e in events)
            and all(artifact_valid(a) for a in artifacts)
            and satisfied("VERIFIED",["verification"])
            and resumable(cp)
            and traceable(prov)
            and passed(v)
        ),"errors":[]}
    }
