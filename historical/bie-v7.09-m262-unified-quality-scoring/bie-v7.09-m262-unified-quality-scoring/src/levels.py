from scoring import weighted_score
from thresholds import evaluate_threshold

def scene_score(checks,weights):
    score=weighted_score(checks,weights)
    return {"score":score,"release":evaluate_threshold(score,90)["release"]}

def lesson_score(scene_results, threshold=92):
    scores=[x["score"] for x in scene_results]
    score=round(sum(scores)/max(1,len(scores)),2)
    return {"score":score,"release":evaluate_threshold(score,threshold)["release"]}

def course_score(lesson_results, threshold=94):
    scores=[x["score"] for x in lesson_results]
    score=round(sum(scores)/max(1,len(scores)),2)
    return {"score":score,"release":evaluate_threshold(score,threshold)["release"]}
