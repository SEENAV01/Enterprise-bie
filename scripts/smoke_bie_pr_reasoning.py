"""Real-process five-stage positive and Math-BLOCKED native synthetic journeys."""
import argparse
import json
from pathlib import Path
import secrets
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def journey(text,expect_math=False):
    from apps.operator.contracts import Credentials,Principal
    from apps.operator.service import Service
    from apps.operator.reasoning_producer import ReasoningProducerControlPlane
    from apps.operator.process_supervision import supervise,child_environment
    from apps.operator.process_limits import PdfProcessBudget
    from bie.productization.pr_reasoning import PROFILE
    from bie.productization.reasoning_slice import STAGES
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tests/productization/document_intelligence"))
    from structural_pdf_fixtures import structural_pdf
    credentials=Credentials();token=secrets.token_urlsafe(40)
    principal=Principal("smoke","local",frozenset({"read","source","create","worker"}),time.time()+180)
    credentials.grant(token,principal)
    with tempfile.TemporaryDirectory(prefix="bie-prod030-") as tmp:
        root=Path(tmp);operator=Service(root,credentials)
        port=ReasoningProducerControlPlane(operator,enabled_profiles={PROFILE})
        source=operator.import_pdf(principal,structural_pdf(text_pages={0},text=text))
        run=port.admit(principal,source["source_id"],"smoke")["run_id"]
        env=child_environment();env["BIE_OPERATOR_TOKEN"]=token
        command=[sys.executable,"-I","-B",str(Path(__file__).resolve().parents[1]/"apps/operator/reasoning_worker_child.py"),
            "--data-root",str(root),"--run-id",run,"--tenant","local"]
        child=supervise(command,env,PdfProcessBudget())
        assert child.completed and child.exit_code==0,"child_execution_failed"
        initial=json.loads(child.output)
        # A second ACTUAL process reopens private state/CAS and verifies identities.
        reopened=supervise(command+["--verify-only"],env,PdfProcessBudget())
        assert reopened.completed and reopened.exit_code==0,"restart_failed"
        final=json.loads(reopened.output)["result"]
        assert initial["result"]==final,"restart_identity_failed"
        replay=ReasoningProducerControlPlane(Service(root,credentials),enabled_profiles={PROFILE}).admit(principal,source["source_id"],"smoke")
        assert replay==final,"idempotency_failed"
        expected={s:"SUCCEEDED" for s in STAGES}
        if expect_math:expected["REASONING"]="BLOCKED"
        assert final["stages"]==expected
        assert all(v=="NOT_RUN" for v in final["downstream"].values())
        with port.native(principal,run,"read") as native:
            snap=native.persistence.load_run_state(run)
            for stage in STAGES:
                a=snap["stages"][stage]["attempts"][-1]
                assert native.queue.get(native.task_id(run,stage,a["attempt"])).state==("DEAD_LETTER" if expect_math and stage=="REASONING" else "ACKED")
                assert a["evidence_refs"]
                for ref in a["output_artifact_refs"]+a["evidence_refs"]:native.record(run,ref)
        if expect_math:assert final["safe_diagnostics"]=={"REASONING":["math_evidence_required"]} and final["reasoning"] is None
        else:assert final["reasoning"]["decision_count"]>0 and final["prerequisite"]["edge_count"]>0
        return dict(passed=True,evidence_kind="SYNTHETIC_TEST",technical_evidence="TECHNICAL_SOURCE_DERIVED",
            stages=final["stages"],source_sha256=source["sha256"],knowledge=final["knowledge"],
            prerequisite=final["prerequisite"],reasoning=final["reasoning"],safe_diagnostics=final["safe_diagnostics"],
            real_child_process=True,restart_in_second_process=True,enforcement=initial["enforcement"],
            idempotent_replay=True,downstream_not_run=True,math_blocked=expect_math,
            product_accepted=False,academic_acceptance=False,live_provider_executed=False)


def run_smoke():
    return dict(passed=True,positive=journey("Birds requires Flight."),
        math_negative=journey("Calculate velocity using v = d / t.",True),product_accepted=False)


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--output",type=Path);args=parser.parse_args()
    try:result=run_smoke()
    except Exception:result=dict(passed=False,code="pr_reasoning_process_smoke_failed",product_accepted=False)
    raw=json.dumps(result,sort_keys=True)+"\n"
    if args.output:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(raw,encoding="utf-8")
    print(raw,end="");return 0 if result["passed"] else 1


if __name__=="__main__":raise SystemExit(main())
