def tokenize(text):
    return set(x.strip(".,!?():;[]{}").lower() for x in (text or "").split() if x)

def lexical_score(query, content):
    q=tokenize(query); c=tokenize(content)
    return len(q & c)/max(1,len(q))

def retrieve(query, evidence, top_k=8):
    ranked=[]
    for e in evidence:
        content=e.get("content","")
        score=lexical_score(query,content)
        if score>0:
            ranked.append({**e,"retrieval_score":round(score,4)})
    ranked.sort(key=lambda x:x["retrieval_score"],reverse=True)
    return ranked[:top_k]
