from backend.graph.graph import KnowledgeGraph

def build_learning_sequence(unit_ids, graph: KnowledgeGraph):
    return graph.topological_order(unit_ids)

def make_lesson(lesson_id, objective, ordered_units, unit_lookup, target_seconds=600):
    n = max(1, len(ordered_units))
    per = target_seconds / n
    sequence = []
    for i, uid in enumerate(ordered_units, 1):
        u = unit_lookup[uid]
        sequence.append({
            "step": i,
            "kind": u.type[0] if u.type else "explanation",
            "unit_ids": [uid],
            "question_types": u.questions,
            "duration_seconds": round(per, 1)
        })
    return {
        "lesson_id": lesson_id,
        "objectives": [objective],
        "prerequisites": sorted({d for uid in ordered_units for d in unit_lookup[uid].dependencies}),
        "knowledge_units": ordered_units,
        "sequence": sequence,
        "applications": [a for uid in ordered_units for a in unit_lookup[uid].applications],
        "misconceptions": [],
        "assessment": [],
        "mastery_criteria": [objective]
    }
