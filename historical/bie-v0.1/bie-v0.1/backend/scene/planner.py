VISUAL_MAP = {
    "definition": "definition",
    "fact": "diagram_or_text",
    "process": "process",
    "mechanism": "process",
    "derivation": "derivation",
    "example": "worked_example",
    "application": "real_world_application",
    "comparison": "comparison",
    "timeline": "timeline",
    "data": "graph",
    "simulation": "simulation"
}

def lesson_to_scenes(lesson, unit_lookup):
    scenes = []
    for step in lesson["sequence"]:
        uid = step["unit_ids"][0]
        u = unit_lookup[uid]
        kind = u.type[0] if u.type else "explanation"
        scenes.append({
            "scene_id": f"SC_{step['step']:04d}",
            "purpose": kind,
            "duration": step["duration_seconds"],
            "content_refs": [uid],
            "visual": {"type": VISUAL_MAP.get(kind, "explanation")},
            "elements": [],
            "animation": {},
            "narration": {"source_unit": uid},
            "equations": [],
            "source_refs": [f"page:{u.source.page}"]
        })
    return scenes
