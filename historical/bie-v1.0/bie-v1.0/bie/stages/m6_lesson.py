
def run(m4, m5):
    units=m4.get("units",[])
    ordered=sorted(units,key=lambda u:(min([r.get("target","") for r in u.get("relations",[])],default=""),u["id"]))
    return {
      "lesson_id":"AUTO-1",
      "objectives":[u["text"] for u in ordered[:8]],
      "sequence":[{"step_id":f"S{i+1:02d}","type":u.get("kind","concept"),"refs":[u["id"]],
                   "source_refs":u.get("source_refs",[])} for i,u in enumerate(ordered)],
      "assessment":[{"type":"application","refs":[u["id"] for u in ordered[-3:]]}],
      "mastery":{"threshold":.85}
    }
