import json
from pathlib import Path
from book_ir import Passage, build_book_ir
from graph_builder import build_learning_graph
from question_matrix import coverage
from scene_planner import plan_scenes

def run(text:str, out_dir:str):
    out=Path(out_dir); out.mkdir(parents=True,exist_ok=True)
    paras=[p.strip() for p in text.split("\n\n") if p.strip()]
    passages=[Passage(f"P{i:04d}",p) for i,p in enumerate(paras,1)]
    ir=build_book_ir(passages)
    graph=build_learning_graph(ir)
    scenes=plan_scenes(ir)
    result={"book_ir":ir,"learning_graph":graph,"question_coverage":coverage(ir),"scene_plan":scenes}
    (out/"pipeline-output.json").write_text(json.dumps(result,indent=2,ensure_ascii=False))
    return result
