def lexical_score(query, terms):
    q=lexical_terms(query)
    return len(q & terms)/max(len(q),1)

def retrieve(query, index, top_k=5):
    ranked=[]
    for item in index:
        ranked.append({"chunk":item["chunk"],"score":lexical_score(query,item["terms"])})
    return sorted(ranked,key=lambda x:(-x["score"],x["chunk"]["chunk_id"]))[:top_k]
