def has_cycle(dependencies):
    g={}
    for d in dependencies:
        g.setdefault(d["source"],[]).append(d["target"])
    visiting=set(); visited=set()

    def dfs(n):
        if n in visiting: return True
        if n in visited: return False
        visiting.add(n)
        for x in g.get(n,[]):
            if dfs(x): return True
        visiting.remove(n); visited.add(n)
        return False

    return any(dfs(n) for n in g)

def check_graph(dependencies):
    return {"has_cycle":has_cycle(dependencies),"status":"INVALID" if has_cycle(dependencies) else "VALID"}
