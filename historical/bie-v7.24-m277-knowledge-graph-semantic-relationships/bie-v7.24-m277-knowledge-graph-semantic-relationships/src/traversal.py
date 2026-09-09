from graph import neighbors

def traverse(graph, start, max_hops=2, predicate=None):
    seen={start}; frontier=[start]; paths=[]
    for hop in range(max_hops):
        nxt=[]
        for node in frontier:
            for r in neighbors(graph,node,predicate):
                other=r["target"] if r["source"]==node else r["source"]
                paths.append({"from":node,"relation":r,"to":other,"hop":hop+1})
                if other not in seen:
                    seen.add(other); nxt.append(other)
        frontier=nxt
        if not frontier: break
    return {"nodes":sorted(seen),"paths":paths}
