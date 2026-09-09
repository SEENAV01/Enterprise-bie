import os, json
from pathlib import Path

DEFAULT_MODEL=os.getenv("BIE_MODEL","gpt-5.6-luna")

SYSTEM="""You are BIE's multimodal book-understanding engine.
Use the supplied document evidence as the authoritative source for source-derived facts.
You may interpret supplied figures, tables and equations, but every resulting claim
must retain an evidence reference. Do not silently correct the source.
Separate source-derived knowledge from higher-knowledge candidates.
Flag ambiguity, unreadable content, conflicting evidence and uncertain visual interpretation.
Return only the requested structured output."""

def build_messages(payload):
    # The adapter deliberately keeps content assembly separate from the API call.
    # A production connector can map visual_assets to image inputs and evidence to text.
    return [
        {"role":"system","content":SYSTEM},
        {"role":"user","content":json.dumps(payload,ensure_ascii=False)}
    ]

def require_key():
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is missing from the environment.")

def api_ready():
    require_key()
    try:
        from openai import OpenAI
    except ImportError:
        return False
    return True
