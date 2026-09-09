def misconception_signal(concept_id,pattern_id,evidence,
                         confidence=None):
    return {"concept_id":concept_id,"pattern_id":pattern_id,
            "evidence":evidence,"confidence":confidence}

def detect_repeated_error(history,wrong_value,minimum=2):
    return {"detected":history.count(wrong_value)>=minimum,
            "count":history.count(wrong_value)}
