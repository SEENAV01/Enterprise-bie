def prerequisite_sequence(target,prerequisite_map):
    ordered=[]; visiting=set(); visited=set()
    def visit(x):
        if x in visiting: raise ValueError("PREREQUISITE_CYCLE")
        if x in visited:return
        visiting.add(x)
        for p in prerequisite_map.get(x,[]): visit(p)
        visiting.remove(x); visited.add(x); ordered.append(x)
    visit(target)
    return ordered

def generate_lesson_sequence(target_concepts,prerequisite_map):
    out=[]
    for t in target_concepts:
        for c in prerequisite_sequence(t,prerequisite_map):
            if c not in out: out.append(c)
    return out
