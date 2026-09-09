def build_boundaries(events, duration_s, min_gap_s=0.15):
    times=sorted({e["time_s"] for e in events if e.get("time_s") is not None})
    boundaries=[]
    for i,t in enumerate(times):
        if i==0 or t-boundaries[-1] >= min_gap_s:
            boundaries.append(t)
    if not boundaries or boundaries[0] > 0:
        boundaries.insert(0,0.0)
    if boundaries[-1] < duration_s:
        boundaries.append(duration_s)
    scenes=[]
    for i in range(len(boundaries)-1):
        if boundaries[i+1]>boundaries[i]:
            scenes.append({
              "scene_id":f"scene_{i+1}",
              "start_s":boundaries[i],
              "end_s":boundaries[i+1]
            })
    return scenes
