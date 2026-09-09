def rubric(objective_id,criteria,levels=None):
    return {"objective_id":objective_id,"criteria":criteria,
            "levels":levels or ["BEGINNING","DEVELOPING","PROFICIENT","ADVANCED"]}

def rubric_score(rubric_data,scores):
    maximum=len(rubric_data["criteria"])*len(rubric_data["levels"])
    total=sum(scores)
    return {"total":total,"maximum":maximum,
            "normalized":total/maximum if maximum else 0}
