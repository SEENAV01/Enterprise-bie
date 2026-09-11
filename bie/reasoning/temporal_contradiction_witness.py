from collections import defaultdict, deque

def contradiction_witness(edges):
    graph = defaultdict(set)
    for a,b in tuple(edges):
        if a == b:
            return (a,a)
        graph[a].add(b)
        graph.setdefault(b,set())
    for start in sorted(graph):
        q = deque([(start,(start,))])
        seen = {start}
        while q:
            n,path = q.popleft()
            for m in sorted(graph[n]):
                if m == start:
                    return path + (m,)
                if m not in seen:
                    seen.add(m)
                    q.append((m,path+(m,)))
    return ()

def is_temporally_consistent(edges):
    return not contradiction_witness(tuple(edges))
