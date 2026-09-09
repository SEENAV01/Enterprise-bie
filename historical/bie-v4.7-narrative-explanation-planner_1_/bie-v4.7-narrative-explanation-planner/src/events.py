EVENT_TYPES=[
"NARRATION","TEXT","EQUATION","DIAGRAM","ANIMATION","HIGHLIGHT",
"EXAMPLE","APPLICATION","QUESTION","PAUSE","TRANSITION","EMPHASIS"
]

def event(event_id,event_type,payload,source_ids=None,depends_on=None):
    return {"id":event_id,"type":event_type,"payload":payload,
            "source_ids":source_ids or [],"depends_on":depends_on or []}
