def build_learning_graph(book_ir:dict)->dict:
    units=book_ir["units"]
    nodes=[u["unit_id"] for u in units]
    edges=[]
    for a,b in zip(nodes,nodes[1:]):
        edges.append({"from":a,"to":b,"relation":"document_order_candidate"})
    return {"nodes":nodes,"edges":edges,
            "note":"Edges are candidates until prerequisite evidence is validated."}

def add_higher_knowledge(book_ir:dict, external_items:list[dict])->dict:
    # External/higher knowledge is explicitly separated from source-derived content.
    for item in external_items:
        target=item.get("unit_id")
        for u in book_ir["units"]:
            if u["unit_id"]==target:
                u["higher_knowledge"].append({
                    "status":"EXTERNAL_RESEARCH",
                    "claim":item["claim"],
                    "evidence":item.get("evidence",[])
                })
    return book_ir
