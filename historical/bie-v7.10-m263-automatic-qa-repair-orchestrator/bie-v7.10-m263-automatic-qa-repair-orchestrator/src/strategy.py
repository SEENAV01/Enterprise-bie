STRATEGIES={
    "ADJUST_TEXT_CONTRAST":{"target":"visual","mode":"patch"},
    "REGENERATE_VISUAL":{"target":"visual","mode":"regenerate"},
    "REBUILD_DIAGRAM_LABELS":{"target":"diagram","mode":"patch"},
    "REBUILD_DIAGRAM_GRAPH":{"target":"diagram","mode":"regenerate"},
    "REGENERATE_AUDIO":{"target":"audio","mode":"regenerate"},
    "NORMALIZE_AUDIO":{"target":"audio","mode":"process"},
    "REGENERATE_OR_RETIME_AUDIO":{"target":"audio","mode":"regenerate_or_retime"},
    "REALIGN_CAPTIONS":{"target":"captions","mode":"realign"},
    "REGENERATE_CAPTIONS":{"target":"captions","mode":"regenerate"},
    "REGENERATE_SEMANTIC_ASSET":{"target":"semantic","mode":"regenerate"},
}
def select_strategies(actions):
    return [{"action":a,**STRATEGIES[a]} for a in actions if a in STRATEGIES]
