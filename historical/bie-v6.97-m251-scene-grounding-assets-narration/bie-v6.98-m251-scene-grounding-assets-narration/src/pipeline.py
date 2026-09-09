from grounding import ground_concept,scene_intent
from assets import rank_asset_candidates,select_asset
from equation_render import render_equation,validate_equation_render
from narration_sync import build_narration_segment,validate_sync
from scene_spec import build_scene_spec,validate_scene_spec

def build_scene_grounding_runtime():
    g=ground_concept("c-field","Electric Field","Explain how a charge creates an electric field.",
                     ["visual","equation","narration"])
    intent=scene_intent(g,"show a point charge and outward field vectors",
                        "Explain that the field describes force per unit charge.",
                        "E = F / q")
    candidates=[
      {"id":"asset-field-vector","type":"diagram","tags":["electric","field","vector"]},
      {"id":"asset-generic","type":"image","tags":["science"]}]
    ranked=rank_asset_candidates(candidates,"diagram",["electric","field","vector"])
    asset=select_asset(ranked)
    eq=render_equation("E = F / q")
    eqcheck=validate_equation_render(eq,"E = F / q")
    narration=build_narration_segment("n1",
        "The electric field is force per unit charge.",0,90,"scene-c-field")
    sync=validate_sync(narration,0,120)
    spec=build_scene_spec(intent,asset,eq,narration)
    validation=validate_scene_spec(spec)
    return {"schema_version":"6.97","grounding":g,"scene_intent":intent,
            "asset_candidates":ranked,"selected_asset":asset,"equation_render":eq,
            "equation_validation":eqcheck,"narration":narration,
            "narration_sync":sync,"scene_spec":spec,"scene_validation":validation,
            "grounding_gate":{"valid":validation["valid"] and eqcheck["valid"] and sync["valid"],
                              "errors":[]}}

def build_m251_runtime():
    return build_scene_grounding_runtime()
