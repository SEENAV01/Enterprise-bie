def targeted_rerender(scene_id, changed_targets):
    # Only scene dependencies affected by repaired targets are selected.
    return {"scene_id":scene_id,"targets":changed_targets,
            "mode":"TARGETED","status":"QUEUED"}

def affected_outputs(dependency_map, changed_targets):
    affected=set()
    for target in changed_targets:
        affected.update(dependency_map.get(target,[]))
    return sorted(affected)
