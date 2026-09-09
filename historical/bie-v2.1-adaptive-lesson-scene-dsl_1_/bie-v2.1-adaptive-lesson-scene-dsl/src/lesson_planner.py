QUESTION_TYPES=["what","why","how","when","where","who","derivation","application"]

def objective_for_node(node):
    typ=node.get("node_type")
    if typ=="law": return f"Explain, apply and reason with {node['label']}."
    if typ=="process": return f"Explain the sequence and mechanism of {node['label']}."
    if typ=="equation": return f"Interpret the variables and derive/use {node['label']}."
    if typ=="application": return f"Connect {node['label']} to a real-world use case."
    return f"Understand and explain {node['label']}."

def coverage_for_node(node, evidence):
    label=node["label"].lower()
    cov=[]
    text=" ".join(x.get("text","").lower() for x in evidence)
    if label in text: cov.append("what")
    if any(k in text for k in ["because","due to","reason"]): cov.append("why")
    if any(k in text for k in ["step","process","method","through"]): cov.append("how")
    if any(k in text for k in ["when","during","time"]): cov.append("when")
    if any(k in text for k in ["where","location","place"]): cov.append("where")
    if any(k in text for k in ["who","scientist","invented"]): cov.append("who")
    if any(k in text for k in ["derive","derivation","therefore"]): cov.append("derivation")
    if any(k in text for k in ["application","used","device","example"]): cov.append("application")
    return sorted(set(cov))

def plan(graph, evidence):
    units=[]
    for n in graph["nodes"]:
        if n["status"] not in {"SOURCE_DERIVED","EXTERNAL"}: continue
        units.append({
            "unit_id":n["node_id"],
            "title":n["label"],
            "objective":objective_for_node(n),
            "question_coverage":coverage_for_node(n,evidence),
            "evidence_refs":n.get("provenance",[]),
            "mastery_gate":0.8
        })
    return units
