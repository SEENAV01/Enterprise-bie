SOURCE_CLASSES=[
"PRIMARY","TEXTBOOK","ACADEMIC_REVIEW","GOVERNMENT",
"STANDARDS_BODY","UNIVERSITY","PROFESSIONAL_ORG",
"REFERENCE","NEWS","GENERAL_WEB"
]
def source_record(source_id,title,url,source_class,published=None,version=None):
    return {"source_id":source_id,"title":title,"url":url,
            "source_class":source_class,"published":published,
            "version":version}
