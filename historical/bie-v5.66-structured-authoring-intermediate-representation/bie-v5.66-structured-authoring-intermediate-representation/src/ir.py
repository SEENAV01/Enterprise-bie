def document_ir(ir_id,title,metadata=None,lessons=None):
    return {"ir_id":ir_id,"type":"DOCUMENT","title":title,
            "metadata":metadata or {},"lessons":lessons or []}

def lesson_ir(lesson_id,title,objectives=None,scenes=None,
              metadata=None):
    return {"lesson_id":lesson_id,"type":"LESSON","title":title,
            "objectives":objectives or [],"scenes":scenes or [],
            "metadata":metadata or {}}
