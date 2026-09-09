from scoring import weighted_score
from thresholds import evaluate_threshold,level_thresholds
from hard_fail import collect_hard_failures

DEFAULT_WEIGHTS={"visual":1.0,"semantic":1.5,"diagram":1.2,
                 "audio":1.0,"captions":1.0,"accessibility":1.2}

def run_scene_qa(results,weights=None,thresholds=None):
    weights=weights or DEFAULT_WEIGHTS
    thresholds=thresholds or level_thresholds()
    score=weighted_score(results,weights)
    hard=collect_hard_failures(results)
    gate=evaluate_threshold(score,thresholds["scene"],hard)
    return {"level":"scene","score":score,"weights":weights,
            "hard_failures":hard,"gate":gate}

def aggregate_lessons(scene_qas,threshold=92):
    scores=[q["score"] for q in scene_qas]
    score=round(sum(scores)/max(1,len(scores)),2)
    return {"level":"lesson","score":score,
            "gate":evaluate_threshold(score,threshold)}

def aggregate_course(lesson_qas,threshold=94):
    scores=[q["score"] for q in lesson_qas]
    score=round(sum(scores)/max(1,len(scores)),2)
    return {"level":"course","score":score,
            "gate":evaluate_threshold(score,threshold)}
