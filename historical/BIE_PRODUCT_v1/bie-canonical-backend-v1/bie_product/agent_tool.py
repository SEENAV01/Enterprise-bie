from __future__ import annotations

BIE_TOOL = {
    "type": "function",
    "name": "bie_book_to_video_code",
    "description": (
        "Use BIE to process an educational book/document into grounded course, "
        "lesson, script, scene and validated video-generation code. BIE preserves "
        "source provenance and returns structured artifacts."
    ),
    "parameters": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "source_path": {"type": "string", "description": "Server-accessible uploaded document path."},
            "task": {"type": "string", "enum": ["book_to_video_code"], "default": "book_to_video_code"}
        },
        "required": ["source_path"]
    },
}

def tool_manifest():
    return {"tools": [BIE_TOOL], "version": "1.0.0"}
