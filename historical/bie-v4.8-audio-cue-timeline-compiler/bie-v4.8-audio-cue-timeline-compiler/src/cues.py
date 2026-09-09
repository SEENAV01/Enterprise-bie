CUE_TYPES=[
"WORD","PHRASE","SENTENCE_START","SENTENCE_END","PAUSE",
"EMPHASIS","EQUATION","HIGHLIGHT","ANIMATION_START",
"ANIMATION_END","SCENE_START","SCENE_END"
]
def cue(cue_id, cue_type, time_s, text=None, confidence=1.0, payload=None):
    return {"id":cue_id,"type":cue_type,"time_s":time_s,
            "text":text,"confidence":confidence,"payload":payload or {}}
