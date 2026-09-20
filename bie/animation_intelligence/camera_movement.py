from .contracts import *
CAMERA_MODES={"pan","zoom","orbit","static_focus","cut"}
def select_camera_movement(ctx, *, focus_target_ids, semantic_need, mode="pan", spatial_context_preserved=True, depth_inspection=False):
    targets=ids(focus_target_ids,"focus_target_ids");semantic_need=tok(semantic_need,"semantic_need")
    if mode not in CAMERA_MODES:raise AnimationSemanticError("unsupported camera mode")
    if ctx.reduced_motion and mode in {"pan","zoom","orbit"}:mode="static_focus"
    if mode=="orbit" and not depth_inspection:return make_decision(ctx,":camera",None,"REVIEW",.55,rationale=("orbit_requires_depth_semantics",))
    if not spatial_context_preserved and mode in {"zoom","orbit"}:return make_decision(ctx,":camera",None,"BLOCKED",.96,rationale=("spatial_context_loss",))
    step=AnimationStep(ctx.intent_id+":camera","camera",targets,ctx.cue.start_ms,ctx.cue.end_ms,"semantic_viewpoint_change",
                       payload={"mode":mode,"semantic_need":semantic_need})
    return make_decision(ctx,":camera","camera","PASS",.88,(step,),("camera_motion_not_decorative",),{"mode":mode,"semantic_need":semantic_need})
