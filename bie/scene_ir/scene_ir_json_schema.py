from .scene_ir_contract import SCENE_IR_SCHEMA_VERSION
def scene_ir_json_schema():
    return {
      "$schema":"https://json-schema.org/draft/2020-12/schema",
      "$id":"https://bie.local/schema/scene-ir/1.0.0",
      "type":"object","additionalProperties":False,
      "required":["scene_id","schema_version","title","duration_ms","elements","tracks","source_refs","reasoning_refs","compiler_capabilities","metadata","review_required","accepted","ir_fingerprint"],
      "properties":{
        "scene_id":{"type":"string","minLength":1},
        "schema_version":{"const":SCENE_IR_SCHEMA_VERSION},
        "title":{"type":"string","minLength":1},
        "duration_ms":{"type":"integer","minimum":1},
        "elements":{"type":"array","minItems":1,"items":{"type":"object"}},
        "tracks":{"type":"array","items":{"type":"object"}},
        "source_refs":{"type":"array","minItems":1,"items":{"type":"string","minLength":1}},
        "reasoning_refs":{"type":"array","minItems":1,"items":{"type":"string","minLength":1}},
        "compiler_capabilities":{"type":"array","items":{"type":"string","minLength":1}},
        "metadata":{"type":"object"},
        "review_required":{"const":True},
        "accepted":{"const":False},
        "ir_fingerprint":{"type":"string","pattern":"^[0-9a-f]{64}$"}
      }
    }
def validate_json_schema_shape(s):
    if s.get("$schema")!="https://json-schema.org/draft/2020-12/schema":raise ValueError("wrong draft")
    if s.get("type")!="object":raise ValueError("root object required")
    must={"scene_id","schema_version","elements","tracks","source_refs","reasoning_refs","ir_fingerprint"}
    if not must.issubset(set(s.get("required",()))):raise ValueError("required fields missing")
    if s["properties"]["schema_version"].get("const")!=SCENE_IR_SCHEMA_VERSION:raise ValueError("version drift")
    return True
SCENE_IR_JSON_SCHEMA=scene_ir_json_schema()
