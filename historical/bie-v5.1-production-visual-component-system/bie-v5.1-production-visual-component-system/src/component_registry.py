from component_api import component_contract

REGISTRY={
"EQUATION":component_contract("Equation","mathematical_reasoning",["expression"]),
"DIAGRAM":component_contract("Diagram","structural_relationship",["nodes","edges"]),
"GRAPH":component_contract("Graph","quantitative_relationship",["x","series"]),
"PROCESS":component_contract("Process","procedural_sequence",["steps"]),
"PARTICLES":component_contract("ParticleSystem","dynamic_flow",["path"]),
"CAMERA":component_contract("Camera","attention_navigation"),
"TEXT":component_contract("KnowledgeText","language_explanation",["text"]),
"HIGHLIGHT":component_contract("Highlight","attention"),
"TRANSITION":component_contract("Transition","scene_change")
}

def get_contract(kind):
    return REGISTRY.get(kind)
