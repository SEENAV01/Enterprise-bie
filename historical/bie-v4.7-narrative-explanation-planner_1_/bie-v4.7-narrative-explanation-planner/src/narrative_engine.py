from narrative_structure import structure_block
from script_planner import build_script_plan
from visual_planner import build_visual_plan
from transition_planner import build_transitions
from narrative_validator import validate

def build_narrative(architecture):
    blocks=architecture.get("blocks",[])
    units={u["knowledge_id"]:u for u in architecture.get("adapted_units",[])}
    structures=[{"block_id":b["id"],"beats":structure_block(b)} for b in blocks]
    script=build_script_plan(blocks,units)
    visuals=build_visual_plan(blocks,units)
    transitions=build_transitions(blocks)
    plan={
      "schema_version":"4.7",
      "blocks":blocks,
      "narrative_beats":structures,
      "script_plan":script,
      "visual_plan":visuals,
      "transitions":transitions,
      "timing_policy":{
        "fixed_duration":False,
        "audio_drives_final_timing":True
      }
    }
    plan["validation"]=validate(plan)
    return plan
