def embedding_contract(asset_id, vector, model):
    return {"asset_id":asset_id,"model":model,"dimensions":len(vector),
            "vector":list(vector),"index_status":"READY"}

def search(query_vector, index, top_k=5):
    def score(v):
        return sum(a*b for a,b in zip(query_vector,v))
    ranked=sorted(index,key=lambda x:score(x["vector"]),reverse=True)
    return ranked[:top_k]
