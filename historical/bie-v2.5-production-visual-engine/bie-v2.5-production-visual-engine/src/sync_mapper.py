def map_markers_to_actions(markers, actions):
    # Production planner can later use semantic token alignment.
    if not markers: return []
    out=[]
    step=max(1,len(markers)//max(1,len(actions)))
    for i,a in enumerate(actions):
        idx=min(len(markers)-1,i*step)
        out.append({
          "action":a,
          "token_index":markers[idx]["token_index"],
          "timestamp_ms":markers[idx].get("timestamp_ms")
        })
    return out
