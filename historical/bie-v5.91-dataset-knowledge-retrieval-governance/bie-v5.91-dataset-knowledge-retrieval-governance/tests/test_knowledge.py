import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from dataset import dataset,snapshot
from documents import document,chunk
from index import index,index_ref
from retrieval import retrieval_query,retrieval_hit,retrieval_evidence
from knowledge_snapshot import knowledge_snapshot,evidence_refs

def test_document_chunk():
 d=document("d1","hash")
 c=chunk("c1","d1","ch",0,10)
 assert c["doc_id"]==d["doc_id"]

def test_index_retrieval():
 i=index("idx","ds","1","embed","3")
 q=retrieval_query("q","hello",index_ref(i))
 h=retrieval_hit({"chunk_id":"c1"},.9,1)
 assert q["index"]["index_id"]=="idx"
 assert retrieval_evidence(q,[h])["hits"][0]["rank"]==1

def test_snapshot():
 ds=dataset("ds","2",["source"])
 ks=knowledge_snapshot("ks",snapshot(ds),
   retrieval_evidence({},[retrieval_hit({"chunk_id":"c1"},.9,1)]),
   "now")
 assert evidence_refs(ks)==["c1"]
