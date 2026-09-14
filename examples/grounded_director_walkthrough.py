"""Reproducible protocol walkthrough; no live model or product acceptance.

python examples/grounded_director_walkthrough.py --output verification/grounded_director.json
"""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys, tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "tests/director"))
from input_fixtures import upstream
from directing_fixtures import executor, orchestrator, context
from bie.director.director_artifacts import fingerprint


def run_case(case_id):
    with tempfile.TemporaryDirectory(prefix="bie-dir-controlled-") as temp:
        f = upstream(temp, case_id); e,g,c,store = executor(f)
        try:
            o = orchestrator(f,e); executed = o.run_until_blocked_or_complete()
            if executed != ["DIRECTOR"]: raise RuntimeError("controlled DIR execution failed")
            current = o.state.stages["DIRECTOR"].current
            output = f.io.load(current.output_artifact_refs[0]); evidence = f.io.load(current.evidence_refs[0])
            result = evidence.payload["result"]
            graph = f.io.load_graph((output.to_ref(),))
            return {"case_id":case_id, "run_id":f.run_id, "fixture_protocol_version":"bie.dir.controlled/1.0.0",
                "upstream_operations_executed":["canonical.teaching_order", "canonical.select_teaching_mode",
                    "canonical.generate_objective", "canonical.build_assessment_blueprint", "canonical.build_pedagogy_plan"]
                    + (["canonical.temporal.event_order"] if case_id == "history" else []),
                "registered_stage":"DIRECTOR", "stage_state":current.state,
                "stage_transitions":[event.to_state for event in o.state.stages["DIRECTOR"].events],
                "artifact_ancestry_count":len(graph), "parent_refs":[asdict(r) for r in f.inputs.parent_refs],
                "output_ref":asdict(output.to_ref()), "execution_evidence_ref":asdict(evidence.to_ref()),
                "generator_calls":len(g.requests), "critic_calls":len(c.requests),
                "scene_count":len(result["plan"]["scenes"]), "utterance_count":len(result["execution"]["snapshot"]["utterances"]),
                "qa_status":evidence.metadata["status"], "release_ready":False, "accepted":False,
                "result_fingerprint":evidence.payload["result_fingerprint"], "result":result}
        finally: store.close()


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--output",type=Path,default=ROOT/"verification/grounded_director.json")
    args=parser.parse_args(); cases=[run_case(k) for k in ("science","economics","history")]
    result={"schema_version":"bie.dir.walkthrough/1.0.0", "cases":cases,
        "scope":"Actual canonical artifact, RE/PED function, orchestration, provider-protocol, narration, QA and timing execution on authored fixtures.",
        "live_model_executed":False, "real_book_pipeline_executed":False, "media_rendered":False,
        "simulation_executed":False, "playable_game_executed":False, "accepted":False,
        "limitations":["Provider output and critic judgments are preauthored protocol fixtures, not model-quality evidence.",
            "Only the supported canonical RE/PED adapters execute; full BI/KI/prerequisite assembly is outside this walkthrough.",
            "Generated assessments have feedback; no learner response or mastery-update loop was executed.",
            "All review flags remain. Timing is estimated and game handoff is metadata; neither is rendered/runtime evidence."]}
    result["walkthrough_fingerprint"]=fingerprint(result)
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"cases":len(cases),"scenes":[c["scene_count"] for c in cases],
        "generator_calls":sum(c["generator_calls"] for c in cases),"critic_calls":sum(c["critic_calls"] for c in cases),
        "statuses":[c["qa_status"] for c in cases],"accepted":False,"fingerprint":result["walkthrough_fingerprint"]}))


if __name__=="__main__": main()
