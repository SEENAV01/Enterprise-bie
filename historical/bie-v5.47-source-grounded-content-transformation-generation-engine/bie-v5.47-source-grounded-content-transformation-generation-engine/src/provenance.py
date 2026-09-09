def provenance_record(output_ref,source_refs=None,
                       generated_refs=None,transform_ref=None,
                       confidence=None):
    return {"output_ref":output_ref,
            "source_refs":source_refs or [],
            "generated_refs":generated_refs or [],
            "transform_ref":transform_ref,
            "confidence":confidence}

def source_coverage(output):
    s=set(output.get("source_refs",[]))
    g=set(output.get("generated_refs",[]))
    return {"source_derived":sorted(s),"generated_additions":sorted(g),
            "mixed":bool(s and g)}
