class IndexError(ValueError): pass
def normalize(entries,page_count):
    out={}
    for term,pages in entries:
        key=str(term).strip()
        if not key: raise IndexError("term")
        vals=tuple(sorted(set(int(p) for p in pages)))
        if any(p<1 or p>page_count for p in vals): raise IndexError("page")
        out[key]=vals
    return out
