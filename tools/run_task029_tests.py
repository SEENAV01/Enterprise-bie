"""Safe unique-count Task029/affected receipts; raw captured failures never uploaded."""
import argparse
from contextlib import redirect_stdout,redirect_stderr
import gc
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import time
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"tests/productization/document_intelligence"))
sys.path.insert(0,str(ROOT/"tests/productization/knowledge"))
sys.path.insert(0,str(ROOT/"tests/section18"))
NEW=["tests/productization/knowledge/test_di_knowledge_producer.py",
     "tests/productization/knowledge/test_di_knowledge_recovery.py"]
AFFECTED=[
 "tests/productization/api/test_pdf_worker_service.py",
 "tests/productization/api/test_local_runtime_stack.py",
 "tests/productization/api/test_local_stack_smoke.py",
 "tests/productization/api/test_posix_port_probe_contract.py",
 "tests/productization/api/test_runtime_stack_restart_repair.py",
 "tests/productization/api/test_persistent_pdf_jobs.py",
 "tests/productization/api/test_pdf_inspection_api.py",
 "tests/productization/document_intelligence/test_real_pdf_text_runtime.py",
 "tests/productization/document_intelligence/test_real_pdf_toc_runtime.py",
 "tests/imported/BIE_INFRA_ORCH_001/tests/enterprise/test_orchestrator.py",
 "tests/imported/BIE_INFRA_STATE_001/tests/enterprise/test_run_state.py",
 "tests/imported/BIE_INFRA_PERSIST_001/tests/enterprise/test_persistence.py",
 "tests/imported/BIE_INFRA_QUEUE_PERSIST_001/tests/enterprise/test_durable_task_queue.py",
 "tests/imported/BIE_INFRA_IDEMP_001/tests/enterprise/test_idempotency_store.py",
 "tests/imported/BIE_INFRA_ARTIFACT_STORE_001/tests/enterprise/test_artifact_store.py",
 "tests/imported/BIE_KI_CONCEPT_001/tests/test_concept_candidates.py",
 "tests/imported/BIE_KI_CLAIM_001/tests/test_claim_extraction.py",
 "tests/imported/BIE_KI_GRAPH_001/tests/test_knowledge_graph_build.py",
 "tests/imported/BIE_KI_GRAPH_002/tests/test_knowledge_graph_validate.py",
 "tests/imported/BIE_KI_E2E_001/tests/test_ki_e2e_pipeline.py",
 "tests/section18/test_batch001.py",
 "tests/section18/test_batch002.py"]


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--lane",choices=("new","affected"),required=True)
    parser.add_argument("--output",type=Path,required=True);args=parser.parse_args()
    results=[];total=failures=errors=skips=0
    for relative in NEW if args.lane=="new" else AFFECTED:
        started=time.monotonic();name="task029_"+hashlib.sha256(relative.encode()).hexdigest()[:16]
        spec=importlib.util.spec_from_file_location(name,ROOT/relative)
        module=importlib.util.module_from_spec(spec);sys.modules[name]=module
        capture=io.StringIO()
        original=unittest.TestCase._callTearDown
        def teardown(case):
            gc.collect()
            return original(case)
        if os.name=="nt":unittest.TestCase._callTearDown=teardown
        try:
            with redirect_stdout(capture),redirect_stderr(capture):
                spec.loader.exec_module(module)
                suite=module.selected_suite() if hasattr(module,"selected_suite") else unittest.defaultTestLoader.loadTestsFromModule(module)
                result=unittest.TextTestRunner(stream=capture).run(suite)
            row=dict(file=relative,tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
                     skips=len(result.skipped),failed_methods=[t.id().split(".")[-1] for t,_ in result.failures+result.errors])
        except Exception:
            row=dict(file=relative,tests=0,failures=0,errors=1,skips=0,failed_methods=["test_import_failed"])
        finally:
            unittest.TestCase._callTearDown=original
        total+=row["tests"];failures+=row["failures"];errors+=row["errors"];skips+=row["skips"]
        row["seconds"]=round(time.monotonic()-started,3);results.append(row)
        print(json.dumps(row,sort_keys=True),flush=True)
        capture.close();gc.collect()
    summary=dict(lane=args.lane,tests=total,failures=failures,errors=errors,skips=skips,
                 passed=not(failures or errors or skips),evidence_kind="TECHNICAL_TEST",
                 windows_teardown_gc=os.name=="nt",product_accepted=False)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(dict(summary=summary,results=results),indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,sort_keys=True));return 0 if summary["passed"] else 1


if __name__=="__main__":raise SystemExit(main())
