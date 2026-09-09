def topological_path(nodes, edges):
    ids=[n["node_id"] for n in nodes]
    indegree={x:0 for x in ids}
    outgoing={x:[] for x in ids}
    for e in edges:
        if e["relation"]=="prerequisite_of" and e["source"] in indegree and e["target"] in indegree:
            outgoing[e["source"]].append(e["target"])
            indegree[e["target"]]+=1
    queue=[x for x in ids if indegree[x]==0]
    path=[]
    while queue:
        x=queue.pop(0); path.append(x)
        for y in outgoing[x]:
            indegree[y]-=1
            if indegree[y]==0: queue.append(y)
    return path if len(path)==len(ids) else None

def recommend_learning_action(mastery, dependency_status):
    if dependency_status!="TRUSTED":
        return "REVIEW_DEPENDENCY"
    if mastery>=.85: return "ADVANCE"
    if mastery>=.60: return "REMEDIATE"
    return "RETEACH_PREREQUISITE"
