ANCHOR_TYPES=[
"SCENE_START","SCENE_END","WORD","PHRASE","PHONEME",
"EMPHASIS","PAUSE","EQUATION_TERM","VISUAL_EVENT"
]

def anchor(anchor_id, anchor_type, start=None, end=None, text=None, metadata=None):
    return {
      "anchor_id":anchor_id,"type":anchor_type,
      "start":start,"end":end,"text":text,
      "metadata":metadata or {}
    }
