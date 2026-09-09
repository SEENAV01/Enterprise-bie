def build_cross_chapter_graph(chapters):
    nodes=[]
    edges=[]
    for ch in chapters:
        for lesson in ch.get("lessons",[]):
            nodes.append(lesson["lesson_id"])
            for dep in lesson.get("depends_on",[]):
                edges.append({"source":dep,"target":lesson["lesson_id"],"type":"PREREQUISITE"})
    return {"nodes":nodes,"edges":edges}
