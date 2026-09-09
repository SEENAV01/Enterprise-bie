
def validate_stage_output(stage, obj):
    if not isinstance(obj, dict): raise TypeError(f"{stage} output must be dict")
    required={
      "M1":["book_id"], "M2":["pages"], "M3":["units"],
      "M4":["nodes","edges"], "M5":["decision"],
      "M6":["sequence"], "M7":["scenes"], "M8":["games"]
    }
    missing=[x for x in required.get(stage,[]) if x not in obj]
    if missing: raise ValueError(f"{stage} missing: {missing}")
    return True
