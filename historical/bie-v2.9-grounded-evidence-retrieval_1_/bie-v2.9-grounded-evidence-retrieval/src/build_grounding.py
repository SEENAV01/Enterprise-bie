import json,sys
from pathlib import Path
from retriever import retrieve
from context_window import build_context
from evidence_ranker import rank_evidence
from grounded_answer import grounded_packet
from contradiction import detect_candidate_conflicts

d=json.loads(Path(sys.argv[1]).read_text())
q=d["query"]
e=d["evidence"]
r=retrieve(q,e)
ranked=rank_evidence(r,q)
context=build_context(ranked,e,window=1)
result=grounded_packet(q,ranked,context)
result["candidate_conflicts"]=detect_candidate_conflicts(context)
Path(sys.argv[2]).write_text(json.dumps(result,indent=2,ensure_ascii=False))
