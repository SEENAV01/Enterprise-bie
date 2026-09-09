def choose_visual(scene):
    typ=scene["type"]
    if typ=="definition": return "mixed"
    if typ in {"causal_explanation","process_animation"}: return "process"
    if typ=="derivation": return "equation"
    if typ=="diagram_explanation": return "diagram"
    if typ=="comparison": return "table"
    if typ=="application": return "real_world"
    if typ=="worked_example": return "mixed"
    if typ=="checkpoint": return "text"
    return scene.get("visual",{}).get("type","mixed")

def build_visual_plan(scene, audio_markers):
    v=choose_visual(scene)
    actions=[]
    if v=="equation":
        actions=["write","highlight_term","substitute","simplify"]
    elif v=="diagram":
        actions=["draw","label_reveal","highlight"]
    elif v=="process":
        actions=["step_reveal","flow","pulse"]
    elif v=="table":
        actions=["reveal_row","highlight_cell","compare_rows"]
    elif v=="real_world":
        actions=["focus","callout"]
    else:
        actions=["fade","highlight","scale"]

    return {
      "scene_id":scene["scene_id"],
      "visual_type":v,
      "actions":actions,
      "sync_strategy":"MARKER_DRIVEN",
      "audio_markers":audio_markers
    }
