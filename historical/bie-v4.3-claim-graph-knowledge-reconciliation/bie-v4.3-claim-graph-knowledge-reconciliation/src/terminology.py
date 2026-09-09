def build_term_map(terms):
    canonical={}
    aliases={}
    for t in terms:
        c=t["canonical"]
        canonical[c]=t
        for a in t.get("aliases",[]):
            aliases[a]=c
    return {"canonical":canonical,"aliases":aliases}

def canonicalize_term(term, term_map):
    return term_map.get("aliases",{}).get(term,term)
