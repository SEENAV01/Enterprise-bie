from script_units import unit

def build_script(lesson_plan, evidence):
    evidence_map={e["evidence_id"]:e for e in evidence}
    out=[]
    i=1

    for b in lesson_plan.get("blocks",[]):
        ev=b.get("evidence_ids",[])
        grounded=[evidence_map[x] for x in ev if x in evidence_map]
        text=b.get("objective","")

        mapping={
          "ORIENTATION":"CONTEXT",
          "PREREQUISITE_REVIEW":"RECAP",
          "DEFINITION":"DEFINITION",
          "INTUITION":"INTUITION",
          "MECHANISM":"MECHANISM",
          "DERIVATION":"DERIVATION_STEP",
          "WORKED_EXAMPLE":"WORKED_EXAMPLE",
          "APPLICATION":"APPLICATION",
          "COMPARISON":"COMPARISON",
          "MISCONCEPTION":"MISCONCEPTION",
          "CHECKPOINT":"QUESTION",
          "TRANSFER":"TRANSFER"
        }
        typ=mapping.get(b["type"],"EXPLANATION")

        source_text=" ".join(x.get("content","") for x in grounded)
        if not source_text and b["type"]!="ORIENTATION":
            continue

        out.append(unit(
          f"u{i}",typ,b.get("objective",""),
          source_text or text,ev,b.get("visual_intent")
        ))
        i+=1

    return {
      "schema_version":"3.4",
      "units":out,
      "script_policy":{
        "grounded_claims_only":True,
        "unsupported_claims":"FLAG",
        "preserve_book_terminology":True
      }
    }
