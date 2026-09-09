def reconstruct_diagram(asset_ref, description, labels=None, relationships=None):
    return {
        "asset_ref":asset_ref,
        "mode":"STRUCTURED_RECONSTRUCTION",
        "description":description,
        "labels":labels or [],
        "relationships":relationships or [],
        "editable":True,
        "provenance":"SOURCE_ASSET"
    }

def diagram_actions(diagram):
    actions=[]
    for label in diagram.get("labels",[]):
        actions.append({"action":"reveal_label","target":label})
    for rel in diagram.get("relationships",[]):
        actions.append({"action":"trace_relationship","target":rel})
    return actions
