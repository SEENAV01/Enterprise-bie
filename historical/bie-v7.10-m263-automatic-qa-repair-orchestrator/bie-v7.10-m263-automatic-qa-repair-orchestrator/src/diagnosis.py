REPAIR_MAP={
    "CONTRAST_BELOW_AA":"ADJUST_TEXT_CONTRAST",
    "AUDIO_CLIPPING":"REGENERATE_AUDIO",
    "AUDIO_LOUDNESS_OUT_OF_RANGE":"NORMALIZE_AUDIO",
    "AUDIO_DURATION_MISMATCH":"REGENERATE_OR_RETIME_AUDIO",
    "CAPTION_OUTSIDE_AUDIO":"REALIGN_CAPTIONS",
    "CAPTION_ORDER_OR_DURATION":"REALIGN_CAPTIONS",
    "DIAGRAM_LABEL_MISSING":"REBUILD_DIAGRAM_LABELS",
    "DIAGRAM_EDGE_REFERENCE":"REBUILD_DIAGRAM_GRAPH",
    "VISUAL_METADATA:resolution":"REGENERATE_VISUAL",
    "SEMANTIC_CRITICAL":"REGENERATE_SEMANTIC_ASSET",
    "AUDIO_MISSING":"REGENERATE_AUDIO",
    "CAPTIONS_MISSING":"REGENERATE_CAPTIONS",
}
def diagnose(errors):
    actions=[]
    for error in errors:
        base=error.split(":",1)[0] if ":" in error else error
        action=REPAIR_MAP.get(error) or REPAIR_MAP.get(base)
        if action and action not in actions: actions.append(action)
    return {"errors":errors,"actions":actions}
