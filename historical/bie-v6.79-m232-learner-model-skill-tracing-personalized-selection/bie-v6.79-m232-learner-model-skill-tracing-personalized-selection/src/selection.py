def select_lessons(lessons,skills,limit=3):
    scored=[]
    for lesson in lessons:
        required=lesson.get("skill_ids",[])
        vals=[skills.get(s,0.0) for s in required]
        mastery=sum(vals)/len(vals) if vals else 1.0
        priority=1.0-mastery
        scored.append((priority,lesson))
    return [l for _,l in sorted(scored,key=lambda x:x[0],reverse=True)[:limit]]
