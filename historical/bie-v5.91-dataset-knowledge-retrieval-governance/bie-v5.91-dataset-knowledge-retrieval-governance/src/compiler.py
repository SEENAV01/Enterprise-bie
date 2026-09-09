from dataset import snapshot
from knowledge_snapshot import knowledge_snapshot,evidence_refs

def compile_knowledge(dataset_record,retrieval_evidence,
                      snapshot_id,created_at):
    ds=snapshot(dataset_record)
    ks=knowledge_snapshot(snapshot_id,ds,
                          retrieval_evidence,created_at)
    return {"schema_version":"5.91",
            "dataset_snapshot":ds,
            "knowledge_snapshot":ks,
            "evidence_refs":evidence_refs(ks),
            "quality_gate":{"valid":True,"errors":[]}}
