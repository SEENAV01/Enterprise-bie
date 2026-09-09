def assembly_order(course):
    chapters=sorted(course.get("chapters",[]),key=lambda x:x.get("order",0))
    return [{"chapter_id":c["chapter_id"],
             "lesson_ids":c.get("lesson_ids",[]),
             "order":c.get("order",0)} for c in chapters]

def course_manifest(course,lessons,chapters,total_frames):
    return {"course_id":course["course_id"],"title":course["title"],
            "chapters":chapters,"lessons":lessons,
            "total_duration_frames":total_frames,
            "status":"READY_FOR_FINAL_ASSEMBLY"}
