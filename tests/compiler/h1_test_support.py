"""Controlled test runtime, NOT React/Remotion render acceptance."""
from pathlib import Path
import json, subprocess, tempfile
from tests.compiler.qa_test_support import ROOT, case_raw

def element(kind,props,*,eid="h1",alt="Synthetic technical test"):
    return {"element_id":eid,"element_type":kind,"props":props,"accessibility":{"alt":alt},"source_refs":["fixture:h1"],"reasoning_refs":["reasoning:h1"]}

def scene(kind,props,*,case_id="physics-vector"):
    raw=case_raw(case_id)["document"];raw.pop("fingerprint",None)
    raw["elements"]=raw["elements"][:1]
    raw["elements"][0]["element_type"]=kind;raw["elements"][0]["props"]=props
    raw["tracks"]=[];raw["capability_requests"]=[];raw["planned_fallbacks"]=[]
    return raw

def runtime_tree(result):
    # Real TypeScript transpilation + explicit React/Remotion TEST doubles.
    with tempfile.TemporaryDirectory() as td:
        request=Path(td)/"request.json"
        request.write_text(json.dumps({"source":result.source_text,"component":result.component_name}))
        run=subprocess.run(["node",str(ROOT/"tests/compiler/h1_jsx_test_runtime.cjs"),str(request)],capture_output=True,text=True,timeout=15)
        if run.returncode:raise AssertionError(run.stderr)
        out=json.loads(run.stdout)
        if out["execution_kind"]!="REAL_TS_TRANSPILATION_WITH_EXPLICIT_JSX_TEST_DOUBLE":raise AssertionError("wrong execution scope")
        return out["tree"]

def nodes(tree,tag):
    out=[]
    if isinstance(tree,dict):
        if tree.get("tag")==tag:out.append(tree)
        for child in tree.get("children",[]):out+=nodes(child,tag)
    elif isinstance(tree,list):
        for child in tree:out+=nodes(child,tag)
    return out

def text_nodes(tree):
    if isinstance(tree,str):return [tree]
    if isinstance(tree,(int,float)):return [str(tree)]
    if isinstance(tree,dict):return sum((text_nodes(c) for c in tree.get("children",[])),[])
    if isinstance(tree,list):return sum((text_nodes(c) for c in tree),[])
    return []
