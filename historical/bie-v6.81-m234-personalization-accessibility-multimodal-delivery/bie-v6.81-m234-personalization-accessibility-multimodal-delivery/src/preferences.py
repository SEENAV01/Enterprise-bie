def learner_preferences(learner_id,language="en",pace="adaptive",
                         visual_density="balanced",caption_required=False):
    return {"learner_id":learner_id,"language":language,"pace":pace,
            "visual_density":visual_density,"caption_required":caption_required}

def validate_preferences(p):
    return bool(p.get("learner_id") and p.get("language"))
