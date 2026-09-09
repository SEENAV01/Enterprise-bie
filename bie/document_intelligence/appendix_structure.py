class AppendixError(ValueError): pass
def validate(items):
    seen=set()
    for a in items:
        aid=str(a.get("id","")); title=str(a.get("title","")).strip(); start=int(a.get("start_page",0)); end=int(a.get("end_page",0))
        if not aid or aid in seen or not title or start<1 or end<start: raise AppendixError("invalid appendix")
        seen.add(aid)
    return tuple(items)
