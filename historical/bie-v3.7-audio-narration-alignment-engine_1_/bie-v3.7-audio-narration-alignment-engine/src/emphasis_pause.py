from alignment_types import anchor

def add_semantic_events(words, emphasis_terms=None, pause_after_words=None):
    emphasis_terms={x.lower() for x in (emphasis_terms or [])}
    pause_after_words=set(pause_after_words or [])
    out=[]
    for w in words:
        if w["type"]=="WORD" and w["text"].strip(".,!?;:").lower() in emphasis_terms:
            out.append(anchor(
              f"e{w['metadata']['word_index']}","EMPHASIS",
              w["start"],w["end"],w["text"],
              {"word_index":w["metadata"]["word_index"]}
            ))
        if w["type"]=="WORD" and w["metadata"]["word_index"] in pause_after_words:
            out.append(anchor(
              f"pause{w['metadata']['word_index']}","PAUSE",
              w["end"],None,None,
              {"after_word":w["metadata"]["word_index"]}
            ))
    return out
