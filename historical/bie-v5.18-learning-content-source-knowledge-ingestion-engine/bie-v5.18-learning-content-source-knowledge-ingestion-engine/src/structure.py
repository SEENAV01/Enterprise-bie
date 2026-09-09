def section(section_id,title,level,parent_id=None,order=0):
    return {"section_id":section_id,"title":title,"level":level,
            "parent_id":parent_id,"order":order,"children":[]}
def build_hierarchy(sections):
    by_id={s["section_id"]:s for s in sections}
    roots=[]
    for s in sections:
        p=s.get("parent_id")
        if p and p in by_id: by_id[p]["children"].append(s["section_id"])
        else: roots.append(s["section_id"])
    return {"sections":by_id,"roots":roots}
