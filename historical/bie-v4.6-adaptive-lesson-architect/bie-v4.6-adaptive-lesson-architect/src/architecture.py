from lesson_blocks import block

def build_architecture(units):
    out=[]
    if not units:return out
    out.append(block("hook","HOOK","Establish relevance or curiosity"))
    out.append(block("objective","OBJECTIVE","State what the learner will be able to do"))
    if any(u.get("prerequisites") for u in units):
        out.append(block("prereq","PREREQUISITE_RECALL","Activate required prior knowledge"))
    for i,u in enumerate(units):
        mode=u.get("teaching_mode","EXPLAIN")
        if mode=="EXPLAIN_WITH_CAUSAL_MODEL":
            btype="MECHANISM"
        elif mode=="DERIVE_STEP_BY_STEP":
            btype="DERIVATION"
        elif mode=="DEMONSTRATE_PROCESS":
            btype="CORE_EXPLANATION"
        elif mode=="SHOW_APPLICATION":
            btype="APPLICATION"
        elif mode=="SHOW_EXAMPLE":
            btype="WORKED_EXAMPLE"
        elif mode=="COMPARE":
            btype="COMPARISON"
        elif mode=="COUNTEREXAMPLE":
            btype="MISCONCEPTION_CHECK"
        else:
            btype="CORE_EXPLANATION"
        out.append(block(f"teach_{i}",btype,u["importance"],
                         [u["knowledge_id"]],mode))
    out.append(block("recap","RECAP","Consolidate the lesson"))
    out.append(block("assessment","ASSESSMENT","Check learner understanding"))
    return out
