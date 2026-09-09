import re

def _sentences(text):
    return [x.strip() for x in re.split(r"(?<=[.!?])\s+", text or "") if x.strip()]

def _find_section(nodes, sid):
    for n in nodes:
        if n.get("section_id") == sid:
            return n
        found = _find_section(n.get("children", []), sid)
        if found:
            return found
    return None

def compile_script(lesson_plan, knowledge, book_structure):
    evidence = knowledge.get("evidence_index", {})
    scenes = []
    script_sections = []

    for unit in lesson_plan.get("units", []):
        source_text = []
        source_blocks = []
        for bid in unit.get("source_evidence", []):
            block = evidence.get(bid)
            if block and block.get("text"):
                source_blocks.append(bid)
                source_text.extend(_sentences(block["text"]))

        if not source_text:
            continue

        # Preserve source-derived statements; no unsupported factual additions.
        narration = " ".join(source_text)
        sid = unit["section_id"]
        script_id = f"script:{sid}"

        script_sections.append({
            "script_id": script_id,
            "unit_id": unit["unit_id"],
            "section_id": sid,
            "title": unit["title"],
            "narration": narration,
            "source_blocks": source_blocks,
            "grounded": True
        })

        scenes.append({
            "scene_id": f"scene:{sid}",
            "script_id": script_id,
            "purpose": unit.get("role", "explanation"),
            "narration": narration,
            "source_blocks": source_blocks
        })

    return {
        "script_ir_version": "1.0",
        "sections": script_sections,
        "scene_candidates": scenes,
        "grounding_policy": "narration is assembled only from selected source evidence",
        "lesson_plan_ref": "lesson_plan",
        "knowledge_ref": "knowledge"
    }

def validate_script(script, knowledge):
    known = set(knowledge.get("evidence_index", {}))
    errors = []
    ids = set()
    for section in script.get("sections", []):
        sid = section.get("script_id")
        if sid in ids:
            errors.append(f"duplicate script_id: {sid}")
        ids.add(sid)
        if not section.get("grounded"):
            errors.append(f"ungrounded script section: {sid}")
        if not section.get("narration"):
            errors.append(f"empty narration: {sid}")
        for bid in section.get("source_blocks", []):
            if bid not in known:
                errors.append(f"unknown source block: {sid}:{bid}")
    for scene in script.get("scene_candidates", []):
        if scene.get("script_id") not in ids:
            errors.append(f"scene references unknown script: {scene.get('scene_id')}")
    return {"passed": not errors, "errors": errors}
