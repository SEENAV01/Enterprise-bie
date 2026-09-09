from prerequisites import topological_order
from sequencing import sequence_events
from curriculum import curriculum

def compile_curriculum(course_id,objectives,concepts,edges,events,assessments):
    ids=[c["concept_id"] for c in concepts]
    graph=topological_order(ids,edges)
    ordered_events=sequence_events(events)
    errors=[]
    if graph["has_cycle"]: errors.append("PREREQUISITE_CYCLE")
    known=set(ids)
    for e in edges:
        if e["from_concept"] not in known or e["to_concept"] not in known:
            errors.append("UNKNOWN_CONCEPT_IN_EDGE")
    return {"schema_version":"5.20",
            "curriculum":curriculum(course_id,objectives,concepts,edges,
                                    ordered_events,assessments),
            "concept_order":graph["order"],
            "quality_gate":{"valid":not errors,"errors":errors}}
