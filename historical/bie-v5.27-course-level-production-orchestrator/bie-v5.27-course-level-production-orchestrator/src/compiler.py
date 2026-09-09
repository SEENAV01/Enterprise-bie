from dependencies import dependency_graph
from incremental import artifact_fingerprint
from parallel import render_batches
from continuity import global_continuity

def compile_course(course_id,lessons,edges,style_token=None,
                   global_assets=None,max_workers=4):
    lesson_ids=[x["lesson_id"] for x in lessons]
    graph=dependency_graph(lesson_ids,edges)
    errors=[]
    if graph["has_cycle"]: errors.append("LESSON_DEPENDENCY_CYCLE")
    batches=render_batches(graph["order"],max_workers)
    style=global_continuity(style_token,global_assets=global_assets or [])
    return {"schema_version":"5.27",
            "course_id":course_id,
            "lesson_order":graph["order"],
            "render_batches":batches,
            "global_continuity":style,
            "fingerprint":artifact_fingerprint(
                {"course_id":course_id,"lessons":lessons,"edges":edges,
                 "style_token":style_token}),
            "quality_gate":{"valid":not errors,"errors":errors}}
