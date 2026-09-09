def assign_bloom(action_verbs):
    verbs=set(v.upper() for v in action_verbs)
    rules=[
      ("CREATE",{"DESIGN","CREATE","CONSTRUCT","PRODUCE"}),
      ("EVALUATE",{"EVALUATE","JUSTIFY","CRITIQUE","ASSESS"}),
      ("ANALYZE",{"ANALYZE","COMPARE","DIFFERENTIATE","EXAMINE"}),
      ("APPLY",{"APPLY","CALCULATE","SOLVE","USE"}),
      ("UNDERSTAND",{"EXPLAIN","DESCRIBE","SUMMARIZE","INTERPRET"}),
      ("REMEMBER",{"DEFINE","IDENTIFY","LIST","RECALL"})]
    for level,words in rules:
        if verbs & words:return level
    return "UNDERSTAND"
