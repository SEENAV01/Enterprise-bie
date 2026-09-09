def align_lesson(lesson_objectives,standard_ids):
    aligned=[o for o in lesson_objectives if set(o.get("standards",[]))&set(standard_ids)]
    coverage=len(aligned)/len(lesson_objectives) if lesson_objectives else 1
    return {"aligned_objectives":[o["objective_id"] for o in aligned],
            "coverage":coverage,"passed":coverage>=0.8}
