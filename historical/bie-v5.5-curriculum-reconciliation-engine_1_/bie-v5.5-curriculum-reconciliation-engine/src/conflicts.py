def detect_conflicts(nodes):
    conflicts=[]
    by_concept={}
    for n in nodes:
        key=n.get("concept_id") or n.get("id")
        by_concept.setdefault(key,[]).append(n)
    for key,items in by_concept.items():
        statements={i.get("statement") for i in items if i.get("statement")}
        if len(statements)>1:
            conflicts.append({
              "concept_id":key,
              "type":"POTENTIAL_CONTRADICTION",
              "statements":sorted(statements)
            })
    return conflicts
