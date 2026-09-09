def hint(question_id,level,text):
    return {"question_id":question_id,"level":level,"text":text}

def select_hint(hints,attempt):
    if not hints: return None
    index=min(max(attempt-1,0),len(hints)-1)
    return hints[index]
