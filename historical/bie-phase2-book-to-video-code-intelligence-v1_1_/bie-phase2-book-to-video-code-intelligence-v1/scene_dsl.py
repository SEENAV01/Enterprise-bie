def _estimate_duration(text, words_per_minute=145, min_seconds=2.0):
    words = len((text or "").split())
    return max(min_seconds, words / max(1, words_per_minute) * 60)

def compile_scene_dsl(script, knowledge):
    """
    Convert grounded script sections into deterministic visual scene specifications.
    Visuals are semantic placeholders, not claims that a renderer has already produced them.
    """
    scenes = []
    for i, section in enumerate(script.get("sections", []), 1):
        sid = section["script_id"]
        narration = section.get("narration", "")
        source_blocks = section.get("source_blocks", [])
        duration = _estimate_duration(narration)

        scenes.append({
            "scene_id": f"visual:{i:04d}",
            "script_id": sid,
            "duration_seconds": round(duration, 2),
            "audio": {
                "type": "narration",
                "text": narration,
                "source_blocks": source_blocks
            },
            "visuals": [
                {
                    "type": "title",
                    "text": section.get("title", ""),
                    "source": "script_section"
                },
                {
                    "type": "source_text",
                    "text": narration,
                    "source_blocks": source_blocks
                }
            ],
            "transitions": {"in":"cut","out":"cut"},
            "grounding": {"source_blocks": source_blocks}
        })

    return {
        "scene_dsl_version": "1.0",
        "canvas": {"width":1920,"height":1080,"fps":30},
        "scenes": scenes,
        "script_ref": "script",
        "grounding_policy": "every factual visual/text element is tied to script source evidence"
    }

def validate_scene_dsl(dsl, script, knowledge):
    errors=[]
    known_script={s.get("script_id") for s in script.get("sections",[])}
    known_blocks=set(knowledge.get("evidence_index",{}))
    ids=set()
    for scene in dsl.get("scenes",[]):
        sid=scene.get("scene_id")
        if sid in ids:
            errors.append(f"duplicate scene_id: {sid}")
        ids.add(sid)
        if scene.get("script_id") not in known_script:
            errors.append(f"unknown script reference: {sid}")
        if scene.get("duration_seconds",0) <= 0:
            errors.append(f"invalid duration: {sid}")
        for bid in scene.get("grounding",{}).get("source_blocks",[]):
            if bid not in known_blocks:
                errors.append(f"unknown source block: {sid}:{bid}")
    return {"passed":not errors,"errors":errors}
