
def run(m4):
    units=m4.get("units",[])
    prov=sum(bool(u.get("source_refs")) for u in units)/len(units) if units else 0
    ext=[]
    for bucket in ("backward","forward","application"):
        ext.extend(m4.get("frontier",{}).get(bucket,[]))
    evidence=sum(bool(x.get("source_refs") or x.get("evidence")) for x in ext)/len(ext) if ext else 1
    coverage=1.0 if units else 0.0
    needs_review=prov<.98 or evidence<.90
    return {"decision":"REVIEW" if needs_review else "PASS",
            "scores":{"coverage":coverage,"provenance":prov,"external_evidence":evidence},
            "needs_review":needs_review}
