"""M3 semantic extraction: document blocks -> source-grounded UBR units.

The extractor deliberately keeps source references attached to every unit. It
uses the OpenAI Responses API when an API key is available, but the schema and
validation layers remain usable without network access for testing.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

QUESTION_TYPES = [
    "WHAT", "WHY", "HOW", "WHEN", "WHERE", "WHO", "WHICH", "HOW_MUCH",
    "HOW_MANY", "WHAT_IF", "WHAT_CAUSES", "WHAT_RESULT", "HOW_DERIVED",
    "UNDER_WHAT_ASSUMPTION", "HOW_DO_WE_KNOW", "WHAT_EVIDENCE", "WHERE_APPLIED",
    "WHY_APPLIED", "COMPARISON", "LIMITATION", "EXCEPTION", "DEPENDENCY",
    "ENABLES", "NEXT_STEP"
]

UNIT_TYPES = [
    "fact", "definition", "claim", "process", "mechanism", "derivation",
    "argument", "example", "counterexample", "exception", "application",
    "evidence", "observation", "comparison", "rule", "condition", "formula",
    "historical_event", "procedure", "unknown"
]

RELATIONS = [
    "IS_A", "PART_OF", "HAS_PART", "REQUIRES", "PREREQUISITE_OF", "CAUSES",
    "CAUSE_OF", "LEADS_TO", "RESULTS_IN", "DERIVED_FROM", "DEPENDS_ON",
    "EXPLAINS", "EXAMPLE_OF", "COUNTEREXAMPLE_OF", "APPLIED_IN", "USED_FOR",
    "SUPPORTED_BY", "EVIDENCED_BY", "CONTRASTS_WITH", "GENERALIZES",
    "SPECIALIZES", "ENABLES", "LIMITED_BY", "EXCEPTION_TO", "PRECEDES", "FOLLOWS"
]

SYSTEM_PROMPT = """You are the semantic extraction engine of a production educational Book Intelligence Engine.
Convert supplied document blocks into a loss-aware, source-grounded intermediate representation.
Do not invent facts. Every unit must cite one or more supplied block ids. Preserve equations and
conditions. Split a paragraph into multiple information units when it contains multiple atomic
claims or relations. Questions describe what the unit answers, not questions you merely imagine.
Use only the allowed enum values. If uncertain, use 'unknown' or omit a relation rather than guess.
Return JSON only matching the requested schema."""

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "units": {
            "type": "array",
            "items": {
                "type": "object", "additionalProperties": False,
                "properties": {
                    "id": {"type": "string"},
                    "type": {"type": "array", "items": {"type": "string", "enum": UNIT_TYPES}},
                    "statement": {"type": "string"},
                    "meaning": {"type": "string"},
                    "questions": {"type": "array", "items": {"type": "string", "enum": QUESTION_TYPES}},
                    "entities": {"type": "array", "items": {"type": "string"}},
                    "source_block_ids": {"type": "array", "items": {"type": "string"}},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                },
                "required": ["id", "type", "statement", "questions", "source_block_ids", "confidence"]
            }
        },
        "relations": {
            "type": "array",
            "items": {
                "type": "object", "additionalProperties": False,
                "properties": {
                    "source_id": {"type": "string"},
                    "relation": {"type": "string", "enum": RELATIONS},
                    "target_id": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                },
                "required": ["source_id", "relation", "target_id", "confidence"]
            }
        }
    },
    "required": ["units", "relations"]
}

@dataclass
class ExtractionResult:
    units: list[dict[str, Any]]
    relations: list[dict[str, Any]]
    warnings: list[str]


def _validate(payload: dict[str, Any], block_ids: set[str]) -> ExtractionResult:
    warnings: list[str] = []
    units = payload.get("units", [])
    relations = payload.get("relations", [])
    ids: set[str] = set()
    clean_units = []
    for u in units:
        uid = str(u.get("id", "")).strip()
        if not uid or uid in ids:
            warnings.append(f"duplicate_or_missing_unit_id:{uid}")
            continue
        ids.add(uid)
        src = [x for x in u.get("source_block_ids", []) if x in block_ids]
        if not src:
            warnings.append(f"unit_without_valid_provenance:{uid}")
            continue
        u["source_block_ids"] = src
        u["confidence"] = max(0.0, min(1.0, float(u.get("confidence", 0.0))))
        clean_units.append(u)
    clean_relations = []
    for r in relations:
        if r.get("source_id") not in ids or r.get("target_id") not in ids:
            warnings.append("relation_with_unknown_unit")
            continue
        clean_relations.append(r)
    return ExtractionResult(clean_units, clean_relations, warnings)


def extract_with_openai(blocks: list[dict[str, Any]], model: str | None = None) -> ExtractionResult:
    """Call the Responses API using Structured Outputs.

    Requires OPENAI_API_KEY. The caller owns retry policy and cost controls.
    """
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set. Configure it before live extraction.")
    from openai import OpenAI
    client = OpenAI()
    model = model or os.getenv("BIE_MODEL", "gpt-5.6")
    compact_blocks = [{
        "block_id": b.get("id"), "page": b.get("page"), "type": b.get("type"),
        "text": b.get("text", ""), "bbox": b.get("bbox")
    } for b in blocks]
    user = "Extract this batch of document blocks.\n\n" + json.dumps(compact_blocks, ensure_ascii=False)
    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": [{"type": "input_text", "text": SYSTEM_PROMPT}]},
            {"role": "user", "content": [{"type": "input_text", "text": user}]}
        ],
        text={"format": {"type": "json_schema", "name": "m3_extraction", "strict": True, "schema": SCHEMA}}
    )
    payload = json.loads(response.output_text)
    return _validate(payload, {str(b.get("id")) for b in blocks})
