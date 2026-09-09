from global_timeline import assign_offsets
from continuity import check_lesson_continuity
from assembly import assembly_order,course_manifest
from validation import validate_course

def compile_course(course,chapters,lessons,lesson_durations,
                   continuity_contract=None,lesson_states=None):
    timed_lessons,total=assign_offsets(lessons,lesson_durations)
    q=validate_course(course,timed_lessons,chapters)
    continuity=[]
    if continuity_contract:
        for state in lesson_states or []:
            continuity.append(check_lesson_continuity(state,continuity_contract))
    errors=q["errors"]+[e for c in continuity for e in c["errors"]]
    manifest=course_manifest(course,timed_lessons,assembly_order(course),total)
    return {"schema_version":"5.15","manifest":manifest,
            "continuity":continuity,
            "quality_gate":{"valid":not errors,"errors":errors}}
