"""Bounded visual projections validated by the actual canonical KI/PR contracts."""
from bie.knowledge_intelligence.knowledge_graph_build import build
from bie.knowledge_intelligence.knowledge_graph_validate import validate
from bie.prerequisite_intelligence.graph import Edge, build_graph, roots
from bie.prerequisite_intelligence.cycle_resolution import WeightedEdge, find_cycle
from .contracts import require, ident, HASH, MAX_NODES, MAX_EDGES

def validate_graph(kind,payload):
    require(kind in ('concept','prerequisite'),'invalid_graph_kind',400)
    require(type(payload) is dict and set(payload)<={'nodes','edges','source_hash','order','roots'} and
            type(payload.get('nodes')) is list and type(payload.get('edges')) is list,'invalid_graph',400)
    nodes,edges = payload['nodes'],payload['edges']
    require(1<=len(nodes)<=MAX_NODES and len(edges)<=MAX_EDGES,'graph_limit',413)
    require(all(type(n) is dict and set(n)=={'id','label'} and type(n['label']) is str and
                0<len(n['label'])<=200 for n in nodes),'invalid_graph_node',400)
    ids = [ident(n['id']) for n in nodes]
    require(len(ids)==len(set(ids)),'duplicate_graph_node',400)
    require(all(type(e) is dict and set(e)=={'source','target','type'} and
                e['source'] in ids and e['target'] in ids and type(e['type']) is str and
                0<len(e['type'])<=64 for e in edges),'invalid_graph_edge',400)
    require(all(e['source']!=e['target'] for e in edges),'graph_self_loop',400)
    require(len({(e['source'],e['target'],e['type']) for e in edges})==len(edges),'duplicate_graph_edge',400)
    ordered_nodes = sorted(nodes,key=lambda n:n['id'])
    ordered_edges = sorted(edges,key=lambda e:(e['source'],e['target'],e['type']))
    # Avoid downstream recursion DoS; capped graph is additionally bounded.
    if kind=='concept':
        graph = build([dict(concept_id=n['id'],label=n['label']) for n in nodes],edges)
        require(validate(graph)['passed'],'canonical_concept_graph_invalid',400)
        return dict(nodes=ordered_nodes,edges=ordered_edges)
    require(all(e['type']=='prerequisite' for e in edges),'invalid_prerequisite_relation',400)
    graph = build_graph(ids,[Edge(e['source'],e['target']) for e in edges])
    require(not find_cycle(set(ids),[WeightedEdge(e['source'],e['target'],1) for e in ordered_edges]),
            'prerequisite_cycle',400)
    remaining = set(ids); complete = set(); order = []
    while remaining:
        ready = sorted(n for n in remaining if graph.incoming[n] <= complete)
        require(bool(ready),'prerequisite_cycle',400)
        order.extend(ready); complete.update(ready); remaining.difference_update(ready)
    return dict(nodes=ordered_nodes,edges=ordered_edges,roots=roots(graph),order=order)
