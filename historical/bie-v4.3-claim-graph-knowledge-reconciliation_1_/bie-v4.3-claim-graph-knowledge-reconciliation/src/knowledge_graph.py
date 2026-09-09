from graph_types import node,edge
from claim_reconciliation import reconcile_claims
from terminology import build_term_map

def build_graph(concepts, claims, sources, terms=None):
    canonical,mappings=reconcile_claims(claims)
    nodes=[]
    edges=[]
    for c in concepts:
        nodes.append(node(c["id"],"CONCEPT",c["label"],c.get("properties")))
    for c in canonical:
        nodes.append(node(c["id"],"CLAIM",c["text"],{
          "status":c["status"],"members":c["members"],
          "evidence_ids":c["evidence_ids"]}))
    for s in sources:
        nodes.append(node(s["source_id"],"SOURCE",s["title"],s))
    for c in canonical:
        for e in c["evidence_ids"]:
            edges.append(edge(c["id"],e,"SOURCED_BY"))
    term_map=build_term_map(terms or [])
    return {
      "schema_version":"4.3",
      "nodes":nodes,
      "edges":edges,
      "claim_mappings":mappings,
      "terminology":term_map,
      "policies":{
        "canonical_claims":True,
        "uncertainty_explicit":True,
        "evidence_linked":True,
        "conflicts_preserved":True
      }
    }
