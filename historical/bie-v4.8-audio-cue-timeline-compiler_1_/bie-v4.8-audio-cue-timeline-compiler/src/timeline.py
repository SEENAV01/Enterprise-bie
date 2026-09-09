def to_frames(seconds,fps):
    return round(seconds*fps)

def compile_timeline(duration_s, fps, mapped_events, scenes):
    return {
      "duration_s":duration_s,
      "fps":fps,
      "duration_frames":to_frames(duration_s,fps),
      "events":[
        {**e,"frame":to_frames(e["time_s"],fps)}
        for e in mapped_events if e.get("time_s") is not None
      ],
      "scenes":[
        {**s,"start_frame":to_frames(s["start_s"],fps),
         "end_frame":to_frames(s["end_s"],fps)}
        for s in scenes
      ]
    }
