from scene_consistency import consistency_check
from reuse import choose_asset
from continuity import continuity_diff

def compile_visual_system(style,grammar,assets,scenes,
                          previous_course_state=None,current_course_state=None):
    checks=[consistency_check(s,style,assets) for s in scenes]
    errors=[e for c in checks for e in c["errors"]]
    warnings=[w for c in checks for w in c["warnings"]]
    continuity=[]
    if previous_course_state and current_course_state:
        continuity=continuity_diff(previous_course_state,current_course_state)
    return {
      "schema_version":"5.10",
      "style_bible":style,
      "visual_grammar":grammar,
      "assets":assets,
      "scenes":scenes,
      "asset_reuse_policy":True,
      "continuity_changes":continuity,
      "quality_gate":{"valid":not errors,"errors":errors,"warnings":warnings}
    }
