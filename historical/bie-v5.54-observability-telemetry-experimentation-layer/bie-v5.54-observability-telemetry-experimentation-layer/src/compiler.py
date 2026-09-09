from observability import quality_summary

def compile_observability(events=None,metrics=None,traces=None,
                          costs=None,latencies=None,experiments=None):
    events=events or []
    validation_events=[e for e in events
                        if e.get("event_type")=="VALIDATION"]
    return {
      "schema_version":"5.54",
      "events":events,"metrics":metrics or [],
      "traces":traces or [],"costs":costs or [],
      "latencies":latencies or [],
      "experiments":experiments or [],
      "summaries":{"validation":quality_summary(validation_events)}
    }
