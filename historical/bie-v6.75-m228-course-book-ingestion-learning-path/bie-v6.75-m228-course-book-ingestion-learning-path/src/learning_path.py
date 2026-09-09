def build_learning_path(chapters,sections,lessons,concept_order):
    chapter_order=[c["chapter_id"] for c in sorted(chapters,key=lambda x:(x.get("number") is None,x.get("number",0)))]
    section_order=[s["section_id"] for s in sorted(sections,key=lambda x:(x.get("number") is None,x.get("number",0)))]
    rank={c:i for i,c in enumerate(concept_order)}
    ordered_lessons=sorted(lessons,key=lambda l:min((rank.get(c,10**9) for c in l["concept_ids"]),default=10**9))
    return {"chapter_order":chapter_order,"section_order":section_order,
            "lesson_order":[l["lesson_id"] for l in ordered_lessons]}

def validate_path(path):
    seq=path["lesson_order"]
    return {"passed":len(seq)==len(set(seq)),"errors":[] if len(seq)==len(set(seq)) else ["DUPLICATE_LESSON"]}
