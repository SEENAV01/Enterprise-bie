def course_progress(lessons):
    total=len(lessons)
    done=sum(1 for x in lessons if x.get("status")=="SUCCEEDED")
    failed=sum(1 for x in lessons if x.get("status")=="FAILED")
    return {"total":total,"completed":done,"failed":failed,
            "percent":round(100*done/max(1,total),2)}

def lesson_progress(scenes):
    total=len(scenes)
    done=sum(1 for x in scenes if x.get("status")=="SUCCEEDED")
    return {"total":total,"completed":done,
            "percent":round(100*done/max(1,total),2)}
