from graph import downstream

def impact_analysis(graph,changed_nodes):
    affected=downstream(graph,changed_nodes)
    return {"changed":changed_nodes,"affected":affected,
            "affected_count":len(affected)}

def classify_artifact(node_type):
    mapping={"concept":"KNOWLEDGE","lesson":"LESSON","scene":"SCENE",
             "visual":"VISUAL","audio":"AUDIO","assessment":"ASSESSMENT",
             "render":"RENDER"}
    return mapping.get(node_type,"ARTIFACT")
