def estimate_tokens(text):
    return max(1,len(text.split()))

def fit_token_budget(parts, budget):
    kept=[]; used=0
    for part in parts:
        cost=estimate_tokens(part)
        if used+cost>budget: break
        kept.append(part); used+=cost
    return {"parts":kept,"used":used,"budget":budget,
            "truncated":len(kept)<len(parts)}
