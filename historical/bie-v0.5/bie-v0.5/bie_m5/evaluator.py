
from collections import defaultdict

WEIGHTS={"DIRECT":1.0,"ENTAILMENT":0.95,"INFERENCE":0.75,"UNSUPPORTED":0.0,"CONTRADICTED":0.0}

def claim_score(claims):
    return 0 if not claims else sum(WEIGHTS.get(c["support"],0)*c["confidence"] for c in claims)/len(claims)

def provenance_score(claims):
    return 0 if not claims else sum(bool(c.get("source_refs")) for c in claims)/len(claims)

def find_cycles(nodes, edges):
    adj=defaultdict(list)
    for e in edges:
        if e["relation"]=="PREREQUISITE_OF": adj[e["source"]].append(e["target"])
    color={}; cycles=[]
    def dfs(u,stack):
        color[u]=1; stack.append(u)
        for v in adj[u]:
            if color.get(v,0)==1:
                i=stack.index(v); cycles.append(stack[i:]+[v])
            elif color.get(v,0)==0: dfs(v,stack)
        stack.pop(); color[u]=2
    for n in nodes:
        if color.get(n,0)==0: dfs(n,[])
    return cycles

def external_evidence_score(nodes,edges):
    ext=[n["id"] for n in nodes if n.get("scope")!="BOOK_INTERNAL"]
    if not ext:return 1.0
    evidenced={e["target"] for e in edges if e.get("target") in ext and e.get("evidence")}
    return len(evidenced)/len(ext)

def evaluate(claims,nodes,edges,coverage=1.0,relation_accuracy=1.0):
    faith=claim_score(claims); prov=provenance_score(claims)
    ext=external_evidence_score(nodes,edges)
    cycles=find_cycles([n["id"] for n in nodes],edges)
    cycle_free=not cycles
    overall=.35*faith+.20*coverage+.15*relation_accuracy+.15*prov+.10*ext+.05*(1 if cycle_free else 0)
    decision="PASS" if overall>=.90 and cycle_free else ("REVIEW" if overall>=.70 else "REJECT")
    return {"faithfulness":round(faith,4),"coverage":round(coverage,4),
            "relation_accuracy":round(relation_accuracy,4),"provenance":round(prov,4),
            "external_evidence":round(ext,4),"cycle_free":cycle_free,
            "overall":round(overall,4),"decision":decision,"cycles":cycles}
