def emphasis_event(event_id,phrase_ref,event_type="STRESS",
                  intensity=1.0):
    return {"event_id":event_id,"phrase_ref":phrase_ref,
            "event_type":event_type,"intensity":intensity}
