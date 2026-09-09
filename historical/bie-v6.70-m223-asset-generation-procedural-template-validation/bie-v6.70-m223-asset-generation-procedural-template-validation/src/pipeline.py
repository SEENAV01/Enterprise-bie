from generation_plan import generation_plan,valid
from template import TemplateRegistry
from procedural import procedural_spec,deterministic
from validation import validate_asset
from multimodal import validate_modalities,validate_semantics
from provenance import provenance

def build_generation_runtime():
    plan=generation_plan(
        "diagram","electric field",
        {"asset_type":"diagram","dimensions":{"width":1920,"height":1080}},
        "VECTOR_TEMPLATE")
    registry=TemplateRegistry()
    registry.register("field-diagram-v1","diagram",
                      ["charge_count","field_lines"],
                      {"charge_count":2})
    instance=registry.instantiate("field-diagram-v1",{"field_lines":12})
    proc=procedural_spec("field-line-generator",42,
                         {"field_lines":12,"charge_count":2})
    generated={"asset_id":"generated-field-001","asset_type":"diagram",
               "uri":"asset://generated-field.svg","width":1920,"height":1080,
               "metadata":{"subject":"electric field"},
               "tags":["electric","field","diagram"],
               "modalities":["vector","visual"]}
    validation=validate_asset(generated,{
        "asset_type":"diagram","dimensions":{"width":1920,"height":1080},
        "metadata":{"subject":"electric field"}})
    modality=validate_modalities(generated,["visual","vector"])
    semantic=validate_semantics(generated,["electric","field","diagram"])
    prov=provenance(generated["asset_id"],"PROCEDURAL",
                    proc["generator"],instance["template_id"],proc["seed"])
    return {"schema_version":"6.70","generation_plan":plan,
            "template_instance":instance,"procedural_spec":proc,
            "generated_asset":generated,"validation":validation,
            "multimodal_validation":modality,
            "semantic_validation":semantic,"provenance":prov,
            "generation_gate":{"valid":(
                valid(plan) and deterministic(proc)
                and validation["passed"] and modality["passed"]
                and semantic["passed"]
            ),"errors":[]}}
