def narration_segment(segment_id,text,objective_ref=None,
                    emphasis=None,pronunciation=None,notes=None):
    return {"segment_id":segment_id,"text":text,
            "objective_ref":objective_ref,
            "emphasis":emphasis or [],
            "pronunciation":pronunciation or {},
            "notes":notes}

def script_block(block_id,segments=None,language="en"):
    return {"block_id":block_id,"segments":segments or [],
            "language":language}
