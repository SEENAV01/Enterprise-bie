def scenes_for_unit(unit, graph_edges):
    scenes=[]
    coverage=unit["question_coverage"]
    if "what" in coverage:
        scenes.append({"type":"definition","objective":"establish the core meaning"})
    if "why" in coverage:
        scenes.append({"type":"causal_explanation","objective":"explain cause/reason"})
    if "how" in coverage:
        scenes.append({"type":"process_animation","objective":"show mechanism/steps"})
    if "derivation" in coverage:
        scenes.append({"type":"derivation","objective":"show mathematical/logical steps"})
    if "application" in coverage:
        scenes.append({"type":"application","objective":"connect to a real-world case"})
    scenes.append({"type":"checkpoint","objective":"test understanding"})
    return scenes

def compile_lesson(units, graph_edges):
    return [{
        **u,
        "scenes":scenes_for_unit(u,graph_edges)
    } for u in units]
