FILLER_WORDS={"um","uh","er","hmm"}
def score_narration(text):
    words=text.split()
    if not words:return {"clarity":0,"conciseness":0,"quality":0}
    filler=sum(w.lower().strip(".,!?") in FILLER_WORDS for w in words)
    clarity=max(0,1-filler/len(words))
    conciseness=max(0,1-max(0,len(words)-35)/100)
    return {"clarity":clarity,"conciseness":conciseness,
            "quality":round((clarity+conciseness)/2,3)}

def validate_narration(text,threshold=0.75):
    s=score_narration(text)
    return {"passed":s["quality"]>=threshold,"score":s,"threshold":threshold}
