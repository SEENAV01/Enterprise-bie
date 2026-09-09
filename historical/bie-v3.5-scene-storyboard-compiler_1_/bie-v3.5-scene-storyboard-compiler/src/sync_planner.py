def build_sync_anchors(scene, narration_text):
    # Architectural contract: exact timestamps are populated after audio analysis.
    words=narration_text.split()
    anchors=[]
    if words:
        anchors.append({"anchor_id":f'{scene["scene_id"]}_start',"semantic":"SCENE_START","word_index":0})
        anchors.append({"anchor_id":f'{scene["scene_id"]}_end","semantic":"SCENE_END","word_index":len(words)-1})
    scene["sync_anchors"]=anchors
    return scene

def timing_contract():
    return {
      "duration":"DERIVE_FROM_AUDIO",
      "minimum_duration":"CONTENT_DEPENDENT",
      "maximum_duration":"NONE",
      "animation_alignment":"SEMANTIC_AUDIO_ANCHORS"
    }
