def check_learning_objective(objective,content_terms):
    terms=set(objective.lower().split()); present=terms&set(content_terms)
    coverage=len(present)/len(terms) if terms else 1
    return {"coverage":coverage,"passed":coverage>=0.5}
def qa_summary(checks):
    failures=[k for k,v in checks.items() if not v.get("passed",False)]
    return {"passed":not failures,"failures":failures}
