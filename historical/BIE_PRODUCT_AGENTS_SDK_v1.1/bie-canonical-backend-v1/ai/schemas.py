BOOK_KNOWLEDGE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "concepts": {"type": "array", "items": {"type": "object", "additionalProperties": False,
            "properties": {
                "id": {"type": "string"}, "label": {"type": "string"},
                "description": {"type": "string"}, "source_refs": {"type": "array", "items": {"type": "string"}}
            }, "required": ["id", "label", "description", "source_refs"]}},
        "relationships": {"type": "array", "items": {"type": "object", "additionalProperties": False,
            "properties": {
                "subject": {"type": "string"}, "predicate": {"type": "string"},
                "object": {"type": "string"}, "evidence_refs": {"type": "array", "items": {"type": "string"}},
                "inferred": {"type": "boolean"}, "confidence": {"type": "number"}
            }, "required": ["subject", "predicate", "object", "evidence_refs", "inferred", "confidence"]}},
        "definitions": {"type": "array", "items": {"type": "object", "additionalProperties": False,
            "properties": {"term": {"type": "string"}, "definition": {"type": "string"}, "source_refs": {"type": "array", "items": {"type": "string"}}},
            "required": ["term", "definition", "source_refs"]}},
        "coverage_notes": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["concepts", "relationships", "definitions", "coverage_notes"]
}

LESSON_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "title": {"type": "string"},
        "objectives": {"type": "array", "items": {"type": "string"}},
        "units": {"type": "array", "items": {"type": "object", "additionalProperties": False,
            "properties": {
                "id": {"type": "string"}, "title": {"type": "string"},
                "concept_ids": {"type": "array", "items": {"type": "string"}},
                "source_refs": {"type": "array", "items": {"type": "string"}},
                "prerequisites": {"type": "array", "items": {"type": "string"}},
                "prerequisite_confidence": {"type": "number"}
            }, "required": ["id", "title", "concept_ids", "source_refs", "prerequisites", "prerequisite_confidence"]}},
        "unresolved_items": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["title", "objectives", "units", "unresolved_items"]
}

SCRIPT_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "sections": {"type": "array", "items": {"type": "object", "additionalProperties": False,
            "properties": {
                "id": {"type": "string"}, "narration": {"type": "string"},
                "source_refs": {"type": "array", "items": {"type": "string"}},
                "concept_ids": {"type": "array", "items": {"type": "string"}}
            }, "required": ["id", "narration", "source_refs", "concept_ids"]}},
        "unresolved_items": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["sections", "unresolved_items"]
}

SCENE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "scenes": {"type": "array", "items": {"type": "object", "additionalProperties": False,
            "properties": {
                "id": {"type": "string"}, "script_ids": {"type": "array", "items": {"type": "string"}},
                "purpose": {"type": "string"}, "visual_type": {"type": "string"},
                "on_screen_text": {"type": "array", "items": {"type": "string"}},
                "visual_instructions": {"type": "array", "items": {"type": "string"}},
                "source_refs": {"type": "array", "items": {"type": "string"}},
                "duration_hint_seconds": {"type": "number"}
            }, "required": ["id", "script_ids", "purpose", "visual_type", "on_screen_text", "visual_instructions", "source_refs", "duration_hint_seconds"]}},
        "unresolved_items": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["scenes", "unresolved_items"]
}
