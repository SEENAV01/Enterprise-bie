def course(course_id,title,metadata=None):
    return {"course_id":course_id,"title":title,"metadata":metadata or {}}

def chapter(chapter_id,title,number=None):
    return {"chapter_id":chapter_id,"title":title,"number":number}

def section(section_id,title,chapter_id,number=None):
    return {"section_id":section_id,"title":title,"chapter_id":chapter_id,"number":number}
