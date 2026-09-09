def adapt_from_diagnosis(report):
    actions=[]
    for r in report:
        if r["status"]=="GAP":
            actions.append({"concept_id":r["concept_id"],"action":"RETEACH",
                            "difficulty":"FOUNDATION","extra_practice":True})
        elif r["status"]=="DEVELOPING":
            actions.append({"concept_id":r["concept_id"],"action":"PRACTICE",
                            "difficulty":"INTERMEDIATE","extra_practice":True})
        else:
            actions.append({"concept_id":r["concept_id"],"action":"PROGRESS",
                            "difficulty":"ADVANCED","extra_practice":False})
    return actions
