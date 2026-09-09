def curriculum(course_id,objectives=None,concepts=None,edges=None,
               events=None,assessments=None):
    return {"course_id":course_id,"objectives":objectives or [],
            "concepts":concepts or [],"prerequisite_edges":edges or [],
            "learning_events":events or [],
            "assessment_targets":assessments or []}
