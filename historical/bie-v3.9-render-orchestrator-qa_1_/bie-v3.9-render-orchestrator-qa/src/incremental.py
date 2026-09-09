def changed_scenes(current_manifest, previous_manifest):
    old={x["scene_id"]:x["fingerprint"] for x in previous_manifest.get("scenes",[])}
    changed=[]
    for x in current_manifest.get("scenes",[]):
        if old.get(x["scene_id"])!=x["fingerprint"]:
            changed.append(x["scene_id"])
    return changed
