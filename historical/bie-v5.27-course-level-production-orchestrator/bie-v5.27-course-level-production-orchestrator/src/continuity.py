def global_continuity(course_style=None,visual_tokens=None,
                      recurring_assets=None):
    return {"style_token":course_style,
            "visual_tokens":visual_tokens or [],
            "recurring_assets":recurring_assets or []}

def check_lesson_continuity(lessons,global_style):
    errors=[]
    for lesson in lessons:
        token=lesson.get("style_token")
        if token and global_style and token!=global_style:
            errors.append({"lesson_id":lesson.get("lesson_id"),
                           "error":"GLOBAL_STYLE_DRIFT"})
    return {"valid":not errors,"errors":errors}
