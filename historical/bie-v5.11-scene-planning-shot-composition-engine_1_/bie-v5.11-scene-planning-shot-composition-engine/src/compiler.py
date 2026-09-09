from planner import plan_shots
from timing import assign_shot_timing
from validation import validate_shot,validate_sequence

def compile_scene_plan(objectives,narration_segments,visuals,assets,
                       style_bible,grammar,transitions=None):
    shots=plan_shots(objectives,narration_segments,visuals,assets,
                     style_bible,grammar)
    shots=assign_shot_timing(shots,narration_segments)
    checks=[validate_shot(s) for s in shots]
    sequence=validate_sequence(shots)
    errors=[e for c in checks for e in c["errors"]]+sequence["errors"]
    return {
      "schema_version":"5.11",
      "shots":shots,
      "transitions":transitions or [],
      "production_metadata":{
        "timing_source":"NARRATION",
        "style_id":style_bible.get("style_id"),
        "visual_grammar_id":grammar.get("grammar_id")
      },
      "quality_gate":{"valid":not errors,"errors":errors}
    }
