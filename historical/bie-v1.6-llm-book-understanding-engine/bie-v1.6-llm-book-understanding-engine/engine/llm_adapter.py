import os, json

SYSTEM_CONTRACT = """You are a source-grounded book understanding engine.
Return ONLY structured JSON matching the supplied schema.
Every source-derived claim must include evidence identifiers.
Do not silently correct the source.
If evidence is insufficient, mark the item unsupported/uncertain.
Keep external knowledge separate as higher_knowledge_candidates.
"""

def require_api_key():
    key=os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set in the environment.")
    return key

def build_request(text:str,schema:dict)->dict:
    return {
      "system":SYSTEM_CONTRACT,
      "input":text,
      "output_schema":schema
    }

def parse_json(text:str)->dict:
    return json.loads(text)
