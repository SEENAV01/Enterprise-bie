"""Credential-free, genuine native-PDF/process/durability technical smoke."""
import argparse
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def run_smoke():
    from apps.operator.contracts import Credentials,Principal
    from apps.operator.service import Service
    from apps.operator.knowledge_producer import KnowledgeProducerControlPlane
    from apps.operator.process_supervision import supervise,child_environment
    from apps.operator.process_limits import PdfProcessBudget
    from bie.productization.contracts import PROFILE
    from bie.productization.durable_slice import KnowledgeProducerService
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tests/productization/document_intelligence"))
    from structural_pdf_fixtures import structural_pdf
    token=secrets.token_urlsafe(40)
    credentials=Credentials()
    principal=Principal("smoke","local",frozenset({"read","source","create","worker"}),time.time()+180)
    credentials.grant(token,principal)
    with tempfile.TemporaryDirectory(prefix="bie-prod029-") as tmp:
        root=Path(tmp)
        operator=Service(root,credentials)
        port=KnowledgeProducerControlPlane(operator,enabled_profiles={PROFILE})
        source=operator.import_pdf(principal,structural_pdf(text_pages={0},text="Gravity attracts objects toward Earth."))
        admitted=port.admit(principal,source["source_id"],"smoke")
        env=child_environment();env["BIE_OPERATOR_TOKEN"]=token
        command=[sys.executable,"-I","-B",str(Path(__file__).resolve().parents[1]/
            "apps/operator/knowledge_worker_child.py"),"--data-root",str(root),
            "--run-id",admitted["run_id"],"--tenant","local"]
        child=supervise(command,env,PdfProcessBudget())
        if not child.completed or child.exit_code!=0:
            raise RuntimeError("native_child_failed")
        receipt=json.loads(child.output)
        if receipt["result"]["stages"]!={s:"SUCCEEDED" for s in ("SOURCE","DOCUMENT_INTELLIGENCE","KNOWLEDGE")}:
            raise RuntimeError("stage_failed")
        # Fresh application/stores after child exit: no in-memory state survives.
        restarted=Service(root,credentials)
        reopened=KnowledgeProducerControlPlane(restarted,enabled_profiles={PROFILE})
        final=reopened.status(principal,admitted["run_id"])
        replay=reopened.admit(principal,source["source_id"],"smoke")
        if final!=receipt["result"] or replay!=final:raise RuntimeError("restart_identity_failed")
        with reopened.native(principal,admitted["run_id"],"read") as native:
            saved=native.persistence.load_run_state(admitted["run_id"])
            for stage in saved["stages"]:
                a=saved["stages"][stage]["attempts"][-1]
                if native.queue.get(native.task_id(admitted["run_id"],stage,a["attempt"])).state!="ACKED":
                    raise RuntimeError("queue_not_acked")
        return dict(passed=True,evidence_kind="SYNTHETIC_TEST",native_pdf=True,
            real_child_process=True,enforcement=receipt["enforcement"],stages=final["stages"],
            knowledge=final["knowledge"],source_sha256=final["source_sha256"],
            restart_identity_preserved=True,idempotent_replay=True,all_tasks_acked=True,
            downstream_not_run=all(v=="NOT_RUN" for v in final["downstream"].values()),
            live_provider_executed=False,academic_acceptance=False,product_accepted=False)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    try:result=run_smoke()
    except Exception:result=dict(passed=False,code="producer_process_smoke_failed",product_accepted=False)
    encoded=json.dumps(result,sort_keys=True)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(encoded,encoding="utf-8")
    print(encoded,end="")
    return 0 if result["passed"] else 1


if __name__=="__main__":raise SystemExit(main())
