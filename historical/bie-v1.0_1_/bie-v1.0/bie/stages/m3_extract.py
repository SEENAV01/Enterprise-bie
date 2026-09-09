
from pathlib import Path
import json
from ..openai_client import structured_response

SCHEMA=json.loads((Path(__file__).parents[2]/"schemas/analysis.schema.json").read_text())

INSTRUCTIONS="""You are BIE M3, a source-grounded book intelligence extractor.
Analyze ONLY the supplied book text. Do not invent facts.
Break the book into atomic information units. For every unit:
- classify the knowledge kind
- identify which question types it answers (what, why, how, when, where, who, what-if, cause, result, application, comparison, limitation, exception, dependency)
- preserve exact page provenance
- state relationships only when supported by the supplied text
Do not add external knowledge here. External knowledge belongs to M4 frontier discovery.
Return only the required JSON schema."""
def run(book):
    payload="\n\n".join(f"[PAGE {p['page']}]\n{p['text']}" for p in book["pages"])
    return structured_response(INSTRUCTIONS,payload,SCHEMA)
