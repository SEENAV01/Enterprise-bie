#!/usr/bin/env python3
from __future__ import annotations
from io import StringIO
from pathlib import Path
import hashlib,importlib,json,shutil,sys,tempfile,unittest,zipfile

ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/"dist"
TASKS=json.loads((ROOT/"metadata/section18/BATCH001_TASKS.json").read_text())["tasks"]
COMMON=[
 "bie/product_app/__init__.py","bie/product_app/source_validation.py","bie/product_app/control_store.py",
 "bie/product_app/operator_service.py","bie/product_app/graph_views.py","bie/product_app/html_views.py",
 "apps/api/operator_routes.py","apps/api/main.py","apps/web/operator.html","tests/section18/helpers.py"
]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run_module(name):
    module=importlib.import_module(name);suite=unittest.defaultTestLoader.loadTestsFromModule(module);stream=StringIO()
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    return {"tests_run":result.testsRun,"failures":len(result.failures),"errors":len(result.errors),"skipped":len(result.skipped),
            "passed":result.wasSuccessful()},stream.getvalue()
def add_file(z,path,arc=None):
    p=ROOT/path
    if p.is_file():z.write(p,arc or path)
def main():
    DIST.mkdir(exist_ok=True)
    atomics=[];total=0
    for task in TASKS:
        result,log=run_module(task["test_module"]);total+=result["tests_run"]
        if not result["passed"]:raise SystemExit("task tests failed: "+task["task_id"])
        out=DIST/(task["task_id"].replace("-","_")+".zip")
        with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
            for p in COMMON:add_file(z,p)
            test_path=task["test_module"].replace(".","/")+".py";add_file(z,test_path)
            spec=(f"# {task['task_id']} — {task['capability']}\n\nCanonical base: 47cafba8975061555764c3c579ae6daad696ae64.\n"
                  "Implementation-scope candidate only; product acceptance is false. See Batch 001 gaps and scope.\n")
            z.writestr("SPEC.md",spec);z.writestr("TEST_RESULT.txt",log)
            z.writestr("TASK_RESULT.json",json.dumps({"task_id":task["task_id"],"capability":task["capability"],
              "tests":result,"section_complete":False,"product_accepted":False},indent=2)+"\n")
        atomics.append({"task_id":task["task_id"],"archive":out.name,"sha256":sha(out),"bytes":out.stat().st_size,"tests":result})
    summary={"schema_version":"1.0.0","batch":"SECTION18_BATCH001","atomic_count":len(atomics),
             "task_test_methods":total,"api_crosscut_tests_module":"tests.section18.test_api_batch001",
             "atomics":atomics,"section_complete":False,"product_accepted":False}
    api_result,api_log=run_module("tests.section18.test_api_batch001")
    if not api_result["passed"]:raise SystemExit("api crosscut tests failed")
    summary["api_crosscut_tests"]=api_result
    (DIST/"BATCH001_TEST_SUMMARY.json").write_text(json.dumps(summary,indent=2)+"\n")
    (DIST/"BATCH001_API_TEST_RESULT.txt").write_text(api_log)
    cont={"schema_version":"1.0.0","section":18,"checkpoint":"BATCH001_LOCAL_VERIFIED",
          "completed_original_tasks":[x["task_id"] for x in TASKS],
          "remaining_original_tasks":23,"next_original_task":"BIE-APP-GRAPH-003",
          "canonical_base_commit":"47cafba8975061555764c3c579ae6daad696ae64",
          "section_complete":False,"product_accepted":False,"task028":"PAUSED"}
    (DIST/"CONTINUATION.json").write_text(json.dumps(cont,indent=2)+"\n")
    master=DIST/"BIE_APP_SECTION18_BATCH001_COMBINED_MASTER_PACKAGE.zip"
    with zipfile.ZipFile(master,"w",zipfile.ZIP_DEFLATED) as z:
        for a in atomics:z.write(DIST/a["archive"],"atomics/"+a["archive"])
        for p in COMMON:add_file(z,p,"combined_source/"+p)
        for p in sorted((ROOT/"tests/section18").glob("*.py")):z.write(p,"combined_source/"+p.relative_to(ROOT).as_posix())
        for p in ["docs/section18/BATCH001_SCOPE.md","metadata/section18/BATCH001_TASKS.json","metadata/section18/BATCH001_GAPS.json"]:
            add_file(z,p,p)
        z.write(DIST/"BATCH001_TEST_SUMMARY.json","evidence/BATCH001_TEST_SUMMARY.json")
        z.write(DIST/"BATCH001_API_TEST_RESULT.txt","evidence/BATCH001_API_TEST_RESULT.txt")
        z.write(DIST/"CONTINUATION.json","CONTINUATION.json")
    print(json.dumps({"master":master.name,"master_sha256":sha(master),"master_bytes":master.stat().st_size,
                      "atomic_count":len(atomics),"task_test_methods":total,"api_crosscut_tests":api_result["tests_run"]},indent=2))
if __name__=="__main__":main()
