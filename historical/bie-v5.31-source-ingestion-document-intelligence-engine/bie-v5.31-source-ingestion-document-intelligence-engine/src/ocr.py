def ocr_result(region_id,text,confidence,engine=None):
    return {"region_id":region_id,"text":text,"confidence":confidence,
            "engine":engine}

def ocr_gate(result,minimum_confidence=0.85):
    return {"valid":result.get("confidence",0)>=minimum_confidence,
            "confidence":result.get("confidence",0),
            "review_required":result.get("confidence",0)<minimum_confidence}
