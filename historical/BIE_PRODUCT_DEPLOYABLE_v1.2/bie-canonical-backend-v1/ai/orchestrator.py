from __future__ import annotations

from typing import Any, Dict, Iterable, List

from .openai_provider import OpenAIProvider
from .bie_prompts import (
    BOOK_KNOWLEDGE_INSTRUCTIONS, LESSON_INSTRUCTIONS,
    SCRIPT_INSTRUCTIONS, SCENE_INSTRUCTIONS,
)
from .schemas import BOOK_KNOWLEDGE_SCHEMA, LESSON_SCHEMA, SCRIPT_SCHEMA, SCENE_SCHEMA


def _trim_blocks(ir: Dict[str, Any], max_chars: int = 60000) -> List[Dict[str, Any]]:
    out, used = [], 0
    for page in ir.get("pages", []):
        for block in page.get("blocks", []):
            text = block.get("text", "")
            if not text and block.get("kind") not in {"FIGURE", "TABLE"}:
                continue
            item = {"page": page.get("page"), "block_id": block.get("block_id"),
                    "kind": block.get("kind"), "text": text}
            cost = len(str(item))
            if used + cost > max_chars:
                return out
            out.append(item); used += cost
    return out


def enrich_knowledge(provider: OpenAIProvider, ir: Dict[str, Any], structure: Dict[str, Any]) -> Dict[str, Any]:
    payload = {"source_uri": ir.get("source_uri"), "book_structure": structure, "source_blocks": _trim_blocks(ir)}
    return provider.generate_json(task="book_knowledge", instructions=BOOK_KNOWLEDGE_INSTRUCTIONS,
                                  input_payload=payload, schema_name="bie_book_knowledge", schema=BOOK_KNOWLEDGE_SCHEMA)


def plan_lesson(provider: OpenAIProvider, knowledge: Dict[str, Any], structure: Dict[str, Any]) -> Dict[str, Any]:
    payload = {"book_structure": structure, "grounded_knowledge": knowledge}
    return provider.generate_json(task="lesson_planning", instructions=LESSON_INSTRUCTIONS,
                                  input_payload=payload, schema_name="bie_lesson_plan", schema=LESSON_SCHEMA)


def compile_script(provider: OpenAIProvider, lesson: Dict[str, Any], knowledge: Dict[str, Any]) -> Dict[str, Any]:
    payload = {"lesson_plan": lesson, "grounded_knowledge": knowledge}
    return provider.generate_json(task="script_generation", instructions=SCRIPT_INSTRUCTIONS,
                                  input_payload=payload, schema_name="bie_script", schema=SCRIPT_SCHEMA)


def compile_scenes(provider: OpenAIProvider, script: Dict[str, Any], lesson: Dict[str, Any]) -> Dict[str, Any]:
    payload = {"lesson_plan": lesson, "script": script}
    return provider.generate_json(task="scene_planning", instructions=SCENE_INSTRUCTIONS,
                                  input_payload=payload, schema_name="bie_scene_plan", schema=SCENE_SCHEMA)
