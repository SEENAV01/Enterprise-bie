def concept_coverage(target_concepts,planned_concepts):
    target=set(target_concepts); planned=set(planned_concepts)
    covered=target & planned
    return {"target_count":len(target),"covered_count":len(covered),
            "coverage":len(covered)/len(target) if target else 1.0,
            "missing":sorted(target-planned)}

def prerequisite_coverage(target_concepts,prerequisite_map,planned_concepts):
    required=set(target_concepts)
    for t in target_concepts:
        stack=list(prerequisite_map.get(t,[]))
        while stack:
            x=stack.pop()
            if x in required: continue
            required.add(x); stack.extend(prerequisite_map.get(x,[]))
    return concept_coverage(required,planned_concepts)
