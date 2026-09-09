from records import memory_record
from provenance import provenance,attach_provenance
from reuse import rank_candidates,reuse_policy
from memory import find_by_concept

def build_memory_record(record_id,record_type,payload,concept_refs=None,
                        source_refs=None,generated_by=None,validated_by=None):
    r=memory_record(record_id,record_type,payload,
                    source_refs=source_refs,concept_refs=concept_refs)
    return attach_provenance(r,provenance(source_refs,
                                          generated_by=generated_by,
                                          validated_by=validated_by))

def reuse_decision(records,concept_id,candidates,threshold=0.85):
    matching=find_by_concept(records,concept_id)
    ranked=rank_candidates(candidates)
    best=ranked[0] if ranked else None
    return {"matching_records":matching,
            "candidates":ranked,
            "decision":reuse_policy(best,threshold) if best else "REGENERATE"}
