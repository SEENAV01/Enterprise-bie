def knowledge_to_game(unit, index=0):
    q = unit.questions[0] if unit.questions else "WHAT"
    mapping = {
        "WHAT": "MCQ", "WHY": "CAUSE_EFFECT", "HOW": "ORDERING", "WHEN": "MCQ",
        "WHERE": "MCQ", "WHICH": "MCQ", "WHAT_IF": "PREDICTION", "HOW_MUCH": "MCQ",
        "HOW_DERIVED": "DERIVATION_ORDERING", "COMPARISON": "MATCHING", "LIMITATION": "ERROR_DETECTION"
    }
    return {
        "game_id": f"G_{index:04d}",
        "type": mapping.get(q, "MCQ"),
        "objective": f"Practice {q} for information unit {unit.id}",
        "difficulty": "core",
        "payload": {"unit_id": unit.id, "question_type": q},
        "source_refs": [f"page:{unit.source.page}"]
    }
