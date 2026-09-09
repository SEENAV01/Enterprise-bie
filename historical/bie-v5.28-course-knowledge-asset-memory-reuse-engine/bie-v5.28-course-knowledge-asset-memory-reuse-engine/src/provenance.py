def provenance(source_refs=None,derived_from=None,
                generated_by=None,validated_by=None):
    return {"source_refs":source_refs or [],
            "derived_from":derived_from or [],
            "generated_by":generated_by,
            "validated_by":validated_by}

def attach_provenance(record,prov):
    out=dict(record); out["provenance"]=prov; return out
