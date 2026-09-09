
from pathlib import Path
import json
from ..openai_client import structured_response

SCHEMA=json.loads((Path(__file__).parents[2]/"schemas/analysis.schema.json").read_text())

INSTRUCTIONS="""You are BIE M4, a knowledge-frontier researcher.
Given verified book units, identify:
1) backward prerequisites outside the book,
2) forward/higher-level knowledge that genuinely builds on the book,
3) real-world applications.
Do not silently turn external knowledge into book content.
Every external candidate must include a concise evidence/source reference and confidence.
Use web search for current/externally verifiable claims.
Prefer authoritative sources. If evidence is weak, mark the candidate as needing review.
Return the same JSON structure; preserve the book units unchanged."""
def run(m3):
    return structured_response(INSTRUCTIONS,json.dumps(m3,ensure_ascii=False),SCHEMA,use_web=True)
