def map_scene_events(scene, aligned_anchors, semantic_map):
    mapped=[]
    for event in scene.get("animation_events",[]):
        key=event.get("sync_key")
        if key and key in semantic_map:
            mapped.append({
              "event":event,
              "anchor_ids":semantic_map[key]
            })
        else:
            mapped.append({"event":event,"anchor_ids":[],"requires_resolution":True})
    scene["sync_events"]=mapped
    return scene

def resolve_word_anchor(anchors, word_index):
    return [a for a in anchors if a.get("metadata",{}).get("word_index")==word_index]
