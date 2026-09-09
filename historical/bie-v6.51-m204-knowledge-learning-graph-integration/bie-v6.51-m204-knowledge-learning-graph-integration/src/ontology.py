def ontology_term(term_id, label, aliases=None,
                 parent_id=None, evidence_ids=None):
    return {"term_id":term_id,"label":label,"aliases":aliases or [],
            "parent_id":parent_id,"evidence_ids":evidence_ids or []}

def consistent(terms):
    labels=[t["label"].strip().lower() for t in terms]
    return len(labels)==len(set(labels))
