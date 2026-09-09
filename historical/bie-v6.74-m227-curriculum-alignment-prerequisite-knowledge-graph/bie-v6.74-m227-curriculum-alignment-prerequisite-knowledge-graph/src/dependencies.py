def dependency_plan(target,graph):
    seen=set(); order=[]
    def visit(n):
        if n in seen:return
        seen.add(n)
        for p in graph.prerequisites(n): visit(p)
        order.append(n)
    visit(target)
    return {"target":target,"ordered_dependencies":order}
