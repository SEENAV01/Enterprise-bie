def asset_relation(source,target,relation_type,
                  metadata=None):
    return {"source":source,"target":target,
            "relation_type":relation_type,
            "metadata":metadata or {}}

def dependents(relations,asset_key_value):
    return [r["target"] for r in relations
            if r.get("source")==asset_key_value]
