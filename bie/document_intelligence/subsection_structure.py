class SubsectionError(ValueError): pass
def validate(nodes,section_ids):
    seen=set()
    for n in nodes:
        if not n.get("id") or n["id"] in seen or n.get("section_id") not in section_ids or not str(n.get("title","")).strip() or int(n.get("order",0))<1:
            raise SubsectionError("invalid subsection")
        seen.add(n["id"])
    return tuple(nodes)
