def make_markers(scene_id, narration):
    # Production TTS/ASR should replace estimates with actual word/phoneme timestamps.
    tokens=[x for x in narration.split() if x]
    return [{
        "scene_id":scene_id,
        "token_index":i,
        "token":t,
        "timestamp_ms":None
    } for i,t in enumerate(tokens)]

def attach_visual_cues(markers, cues):
    # cues: [{"token_index": 3, "action": "highlight"}]
    by={x["token_index"]:x["action"] for x in cues}
    return [{**m,"visual_action":by.get(m["token_index"])} for m in markers]
