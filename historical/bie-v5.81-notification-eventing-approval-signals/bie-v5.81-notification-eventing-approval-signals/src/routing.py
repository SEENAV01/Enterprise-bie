def route_event(evt,subscriptions):
    return subscriptions.get(evt.get("event_type"),[])

def approval_signal(evt):
    return evt.get("event_type") in {
      "REVIEW_APPROVED","REVIEW_REJECTED",
      "REVIEW_ESCALATED","OVERRIDE_CREATED"
    }
