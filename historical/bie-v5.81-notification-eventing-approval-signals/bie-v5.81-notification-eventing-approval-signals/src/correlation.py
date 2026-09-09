def correlation_chain(events,correlation_id):
    return [e for e in events
            if e.get("correlation_id")==correlation_id]

def caused_by(events,event_id):
    return [e for e in events if e.get("causation_id")==event_id]
