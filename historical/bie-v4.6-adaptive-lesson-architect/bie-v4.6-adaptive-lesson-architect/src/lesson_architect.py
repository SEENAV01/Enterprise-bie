from architecture import build_architecture
from presentation_decider import presentation_plan
from assessment_planner import assessment_for
from timing_policy import timing_requirements
from adaptation import adapt_unit

def architect(units, learner=None):
    learner=learner or {}
    adapted=[adapt_unit(u,learner) for u in units]
    blocks=build_architecture(adapted)
    by_id={u["knowledge_id"]:u for u in adapted}
    presentations=presentation_plan(blocks,by_id)
    assessments=[
      {"knowledge_id":u["knowledge_id"],
       "assessment_types":assessment_for(u)}
      for u in adapted
    ]
    timing=[{"block_id":b["id"],
             **timing_requirements(b)}
             for b in blocks]
    return {
      "schema_version":"4.6",
      "blocks":blocks,
      "adapted_units":adapted,
      "presentation_plan":presentations,
      "assessment_plan":assessments,
      "timing_requirements":timing,
      "policy":{
        "audio_drives_final_timing":True,
        "no_fixed_duration_per_concept":True,
        "adaptation_supported":True,
        "assessment_integrated":True
      }
    }
