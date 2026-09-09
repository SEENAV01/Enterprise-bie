def plan_presentation(scene, audio_duration_ms):
    # Duration is not constrained by a fixed scene budget.
    # Presentation is allocated around explanation and audio.
    kind=scene["type"]
    actions=[]
    if kind in {"definition","causal_explanation"}:
        actions=["introduce","visualize","emphasize_key_term","pause_for_comprehension"]
    elif kind in {"process_animation","diagram_explanation"}:
        actions=["orient","show_step_by_step","highlight_relationships","pause"]
    elif kind=="derivation":
        actions=["state_target","introduce_variables","derive_stepwise","verify_result"]
    elif kind in {"application","worked_example"}:
        actions=["introduce_context","map_principle","work_through","state_takeaway"]
    elif kind=="checkpoint":
        actions=["present_question","pause_for_response","reveal_or_explain"]
    else:
        actions=["explain","reinforce"]
    return {
        "scene_id":scene["scene_id"],
        "audio_duration_ms":audio_duration_ms,
        "presentation_actions":actions,
        "timing_policy":"CONTENT_DRIVEN_NO_FIXED_MAX_DURATION",
        "minimum_readability":True
    }
