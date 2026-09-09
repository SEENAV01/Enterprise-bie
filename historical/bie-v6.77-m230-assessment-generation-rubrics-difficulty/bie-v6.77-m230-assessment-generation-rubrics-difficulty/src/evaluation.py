def evaluation_plan(items):
    return [{"item_id":i["item_id"],"objective_id":i["objective_id"],
             "difficulty":i.get("difficulty","MEDIUM"),
             "scoring":"RUBRIC" if i["item_type"]=="OPEN" else "ANSWER_KEY"}
            for i in items]

def coverage(items,objective_ids):
    covered={i["objective_id"] for i in items}
    required=set(objective_ids)
    return {"covered":sorted(covered&required),
            "missing":sorted(required-covered),
            "coverage":len(covered&required)/len(required) if required else 1}
