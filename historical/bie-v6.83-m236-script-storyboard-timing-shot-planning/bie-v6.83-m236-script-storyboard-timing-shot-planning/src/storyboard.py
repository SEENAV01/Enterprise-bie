def shot(shot_id,segment_id,shot_type,visual,transition="CUT"):
    return {"shot_id":shot_id,"segment_id":segment_id,"shot_type":shot_type,
            "visual":visual,"transition":transition}

def storyboard(script_segments,asset_plan=None):
    asset_plan=asset_plan or []
    shots=[]
    for i,s in enumerate(script_segments):
        visual=asset_plan[i].get("description",s["text"]) if i<len(asset_plan) else s["text"]
        shots.append(shot(f"SHOT-{i+1}",s["segment_id"],"EXPLANATION",visual))
    return shots
