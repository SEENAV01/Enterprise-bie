"""Actual native PDF Math/no-Math/review journeys and second-process reopen."""
import argparse
import json
from pathlib import Path
import secrets
import sys
import tempfile
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


class SmokeFailure(Exception):
    def __init__(self, phase, code):
        self.phase=phase;self.code=code


def require(condition,phase,code):
    if not condition:raise SmokeFailure(phase,code)


def journey(lines,applicability):
    from apps.operator.contracts import Credentials,Principal
    from apps.operator.service import Service
    from apps.operator.math_producer import MathProducerControlPlane
    from apps.operator.process_supervision import supervise,child_environment
    from apps.operator.process_limits import PdfProcessBudget
    from bie.productization.math_evidence import PROFILE
    from bie.productization.math_slice import STAGES
    sys.path.insert(0,str(ROOT/"tests/productization/document_intelligence"))
    from structural_pdf_fixtures import positioned_text_pdf
    credentials=Credentials();token=secrets.token_urlsafe(40)
    principal=Principal("smoke","local",frozenset({"read","source","create","worker"}),time.time()+180)
    credentials.grant(token,principal)
    raw=positioned_text_pdf([[(72,740-40*i,text) for i,text in enumerate(("Birds requires Flight.",)+tuple(lines))]])
    with tempfile.TemporaryDirectory(prefix="bie-prod031-") as tmp:
        root=Path(tmp);operator=Service(root,credentials)
        port=MathProducerControlPlane(operator,enabled_profiles={PROFILE})
        source=operator.import_pdf(principal,raw)
        run=port.admit(principal,source["source_id"],"smoke")["run_id"]
        env=child_environment();env["BIE_OPERATOR_TOKEN"]=token
        command=[sys.executable,"-I","-B",str(ROOT/"apps/operator/math_worker_child.py"),
            "--data-root",str(root),"--run-id",run,"--tenant","local"]
        child=supervise(command,env,PdfProcessBudget())
        require(child.completed,applicability,"child_supervision_incomplete")
        require(child.exit_code==0,applicability,"child_execution_failed")
        initial=json.loads(child.output)
        reopened=supervise(command+["--verify-only"],env,PdfProcessBudget())
        require(reopened.completed and reopened.exit_code==0,applicability,"restart_failed")
        final=json.loads(reopened.output)["result"]
        assert initial["result"]==final,"restart_identity_failed"
        assert port.admit(principal,source["source_id"],"smoke")==final,"replay_failed"
        blocked=applicability=="REVIEW_REQUIRED"
        expected={s:"SUCCEEDED" for s in STAGES}
        if blocked:expected.update(MATH="BLOCKED",REASONING="PENDING")
        assert final["stages"]==expected and final["math"]["applicability"]==applicability
        assert all(v=="NOT_RUN" for v in final["downstream"].values())
        with port.native(principal,run,"read") as native:
            snap=native.persistence.load_run_state(run)
            for stage in STAGES:
                a=snap["stages"][stage]["attempts"][-1]
                if blocked and stage=="REASONING":
                    assert not a["output_artifact_refs"] and not a["evidence_refs"];continue
                assert native.queue.get(native.task_id(run,stage,a["attempt"])).state==("DEAD_LETTER" if blocked and stage=="MATH" else "ACKED")
                assert a["evidence_refs"]
                for ref in a["output_artifact_refs"]+a["evidence_refs"]:native.record(run,ref)
        if not blocked:
            assert final["reasoning"]["math_artifact_id"]==final["math"]["artifact_id"]
            assert final["reasoning"]["math_sha256"]==final["math"]["sha256"]
        else:assert final["reasoning"] is None and not final["slice_complete"]
        return dict(passed=True,evidence_kind="SYNTHETIC_TEST",technical_evidence="TECHNICAL_SOURCE_DERIVED",
            source_sha256=source["sha256"],stages=final["stages"],math=final["math"],reasoning=final["reasoning"],
            native_pdf=True,real_child_process=True,restart_in_second_process=True,
            artifact_identity_preserved=True,queue_terminal_states_verified=True,
            enforcement=initial["enforcement"],idempotent_replay=True,downstream_not_run=True,
            academic_acceptance=False,product_accepted=False,live_provider_executed=False)


def run_smoke():
    result=dict(passed=True,product_accepted=False)
    for label,lines,applicability in (("supported_math",("2 + 3 = 5",),"REQUIRED"),
            ("non_math",(),"NOT_REQUIRED"),
            ("unsupported_math",("Compute the matrix inverse.",),"REVIEW_REQUIRED")):
        try:result[label]=journey(lines,applicability)
        except SmokeFailure:raise
        except Exception:raise SmokeFailure(label,"journey_verification_failed") from None
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--output",type=Path);args=parser.parse_args()
    try:result=run_smoke()
    except SmokeFailure as error:
        result=dict(passed=False,phase=error.phase,code=error.code,product_accepted=False)
    except Exception:result=dict(passed=False,code="math_process_smoke_failed",product_accepted=False)
    raw=json.dumps(result,sort_keys=True)+"\n"
    if args.output:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(raw,encoding="utf-8")
    print(raw,end="");return 0 if result["passed"] else 1


if __name__=="__main__":raise SystemExit(main())
