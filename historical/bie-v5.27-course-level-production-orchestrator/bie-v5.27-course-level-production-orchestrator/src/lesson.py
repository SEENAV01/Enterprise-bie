def lesson_manifest(lesson_id,title,order,scenes=None,
                    dependencies=None,artifacts=None):
    return {"lesson_id":lesson_id,"title":title,"order":order,
            "scenes":scenes or [],"dependencies":dependencies or [],
            "artifacts":artifacts or []}
