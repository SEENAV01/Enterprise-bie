def course(course_id,title,chapters=None,global_style_id=None):
    return {"course_id":course_id,"title":title,"chapters":chapters or [],
            "global_style_id":global_style_id,"metadata":{}}

def chapter(chapter_id,title,lesson_ids=None,order=0):
    return {"chapter_id":chapter_id,"title":title,
            "lesson_ids":lesson_ids or [],"order":order}

def lesson(lesson_id,title,scene_ids=None,order=0):
    return {"lesson_id":lesson_id,"title":title,
            "scene_ids":scene_ids or [],"order":order}
