from collections import defaultdict, deque

RELATION_TYPES = {
    "IS_A", "PART_OF", "HAS_PART", "REQUIRES", "PREREQUISITE_OF", "CAUSES", "CAUSE_OF",
    "LEADS_TO", "RESULTS_IN", "DERIVED_FROM", "DEPENDS_ON", "EXPLAINS", "EXAMPLE_OF",
    "COUNTEREXAMPLE_OF", "APPLIED_IN", "USED_FOR", "SUPPORTED_BY", "EVIDENCED_BY",
    "CONTRASTS_WITH", "GENERALIZES", "SPECIALIZES", "ENABLES", "LIMITED_BY", "EXCEPTION_TO",
    "PRECEDES", "FOLLOWS"
}

class KnowledgeGraph:
    def __init__(self):
        self.edges = defaultdict(list)

    def add_edge(self, source, relation, target, confidence=1.0):
        if relation not in RELATION_TYPES:
            raise ValueError(f"Unknown relation: {relation}")
        self.edges[source].append((relation, target, confidence))

    def prerequisites(self, node):
        return [target for rel, target, _ in self.edges.get(node, []) if rel in {"REQUIRES", "PREREQUISITE_OF", "DEPENDS_ON"}]

    def topological_order(self, nodes):
        nodes = set(nodes)
        indegree = {n: 0 for n in nodes}
        outgoing = defaultdict(list)
        for s in nodes:
            for rel, t, _ in self.edges.get(s, []):
                if t in nodes and rel in {"PRECEDES", "PREREQUISITE_OF", "REQUIRES"}:
                    outgoing[s].append(t); indegree[t] += 1
        q = deque(sorted([n for n, d in indegree.items() if d == 0]))
        result = []
        while q:
            n = q.popleft(); result.append(n)
            for t in outgoing[n]:
                indegree[t] -= 1
                if indegree[t] == 0: q.append(t)
        if len(result) != len(nodes):
            raise ValueError("Learning graph contains a dependency cycle")
        return result
