def build_timeline(ir):
    return {
      "mode":"AUDIO_DRIVEN",
      "sync_events":[
        {"event":e,"anchor_ids":e.get("anchor_ids",[])}
        for e in ir.get("events",[])
      ],
      "duration_source":"AUDIO_ALIGNMENT",
      "fixed_duration":False
    }
