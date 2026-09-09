def concept_coverage(concept_ids,objectives):
    covered=set()
    for o in objectives: covered.update(o.get("concept_ids",[]))
    required=set(concept_ids)
    return {"covered":sorted(covered&required),
            "missing":sorted(required-covered),
            "coverage":len(covered&required)/len(required) if required else 1.0}

def objective_coverage(concept_ids,objectives):
    required=set(concept_ids)
    return {"objective_count":len(objectives),
            "objectives_with_concepts":sum(bool(set(o.get("concept_ids",[]))&required) for o in objectives)}
