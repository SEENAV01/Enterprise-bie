from pacing import pace
from spaced_review import next_review
from forgetting import retention,forgetting_risk
from sequencing import sequence_lessons,session_plan

def build_adaptive_experience():
    masteries={"charge":0.9,"field":0.55,"force":0.35}
    risks={s:forgetting_risk(m,days_since_review=days)
           for s,m,days in [("charge",0.9,10),("field",0.55,4),("force",0.35,2)]}
    review_dates={s:next_review(m,10 if s=="charge" else (4 if s=="field" else 2))
                  for s,m in masteries.items()}
    pace_info=pace(masteries,20)
    lessons=[
      {"lesson_id":"force-reteach","skill_ids":["force"]},
      {"lesson_id":"field-review","skill_ids":["field"]},
      {"lesson_id":"charge-advanced","skill_ids":["charge"]}]
    risk_scores={s:v["risk"] for s,v in risks.items()}
    ordered=sequence_lessons(lessons,masteries,risk_scores)
    session=session_plan(lessons,masteries,pace_info)
    return {"schema_version":"6.80","masteries":masteries,
            "forgetting_risk":risks,"review_schedule":review_dates,
            "pacing":pace_info,"lesson_sequence":ordered,
            "session_plan":session,
            "adaptive_experience_gate":{"valid":(
                0<pace_info["recommended_minutes"]<=60 and
                len(ordered)==len(lessons) and
                all(0<=v["predicted_retention"]<=1 for v in risks.values())
            ),"errors":[]}}
