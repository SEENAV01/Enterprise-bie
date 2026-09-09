def segment(segment_id, source_id, page=None, order=0, text=None, layout=None):
    return {"segment_id":segment_id,"source_id":source_id,"page":page,
            "order":order,"text":text,"layout":layout or {}}

def ordered(records):
    return sorted(records,key=lambda x:(x["page"] or 0,x["order"]))
