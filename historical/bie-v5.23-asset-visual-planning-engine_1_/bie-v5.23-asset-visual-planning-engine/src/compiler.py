from selection import select_modality
from visual_spec import visual_spec
from animation import animation_plan
from renderability import renderability_check

def compile_visual_plan(concept_id,concept_type,objective_level,
                        objective_id=None,learner_preference="BEST_FIT",
                        primitives=None,source_refs=None):
    m=select_modality(concept_type,objective_level,learner_preference)
    spec=visual_spec("vs-"+concept_id,concept_id,m,objective_id,
                     primitives,animation_plan(),
                     ["SYNC_TO_NARRATION"],source_refs)
    check=renderability_check(spec)
    return {"schema_version":"5.23","visual_spec":spec,
            "quality_gate":check}
