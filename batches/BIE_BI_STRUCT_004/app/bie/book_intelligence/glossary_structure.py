class GlossaryError(ValueError): pass
def normalize(entries):
    out={}; aliases={}
    for e in entries:
        term=str(e.get("term","")).strip(); definition=str(e.get("definition","")).strip()
        if not term or not definition: raise GlossaryError("term/definition")
        key=term.casefold()
        if key in out and out[key]["definition"]!=definition: raise GlossaryError("conflicting definition")
        out[key]={"term":term,"definition":definition,"source_anchor":e.get("source_anchor")}
        for a in e.get("aliases",[]): aliases[str(a).casefold()]=key
    return out,aliases
