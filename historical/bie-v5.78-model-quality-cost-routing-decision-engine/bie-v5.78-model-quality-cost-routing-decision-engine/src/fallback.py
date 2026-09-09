def fallback_chain(ranked,primary_id=None):
    ids=[m["model_id"] for m in ranked]
    if primary_id in ids:
        ids.remove(primary_id)
        ids.insert(0,primary_id)
    return ids

def next_fallback(chain,failed_id):
    try: i=chain.index(failed_id)
    except ValueError: return None
    return chain[i+1] if i+1<len(chain) else None
