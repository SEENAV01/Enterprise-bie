from graph import dependency_graph
from impact import impact_analysis
from regeneration import minimal_plan
from safety import source_change_gate

def compile_impact_plan(nodes,edges,changed_nodes,
                        change_type="UPDATE",confidence=1.0,
                        protected=None):
    graph=dependency_graph(nodes,edges)
    gate=source_change_gate(change_type,confidence)
    impact=impact_analysis(graph,changed_nodes)
    plan=minimal_plan(changed_nodes,impact["affected"],protected)
    if gate["status"]=="BLOCK":
        plan=[]
    return {"schema_version":"5.29",
            "change_gate":gate,
            "impact":impact,
            "regeneration_plan":plan,
            "quality_gate":{"valid":gate["status"]!="BLOCK",
                            "errors":[] if gate["status"]!="BLOCK"
                            else [gate["reason"]]}}
