
import json, os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def client():
    return OpenAI()

def structured_response(instructions, payload, schema, model=None, use_web=False):
    model=model or os.getenv("BIE_MODEL","gpt-5.6-luna")
    kwargs={
      "model":model,
      "instructions":instructions,
      "input":payload,
      "text":{"format":{
        "type":"json_schema",
        "name":"bie_result",
        "strict":True,
        "schema":schema
      }}
    }
    if use_web:
        kwargs["tools"]=[{"type":"web_search"}]
    r=client().responses.create(**kwargs)
    return json.loads(r.output_text)
