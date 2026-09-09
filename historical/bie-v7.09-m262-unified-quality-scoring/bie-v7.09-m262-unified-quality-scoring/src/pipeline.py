from qa_engine import run_scene_qa,aggregate_lessons,aggregate_course

def build_m262_runtime():
    checks={"visual":{"valid":True,"errors":[]},
            "semantic":{"valid":True,"errors":[]},
            "diagram":{"valid":True,"errors":[]},
            "audio":{"valid":True,"errors":[]},
            "captions":{"valid":True,"errors":[]},
            "accessibility":{"valid":True,"errors":[]}}
    scene1=run_scene_qa(checks)
    scene2=run_scene_qa(checks)
    lesson=aggregate_lessons([scene1,scene2])
    course=aggregate_course([lesson])
    valid=scene1["gate"]["release"] and lesson["gate"]["release"] and course["gate"]["release"]
    return {"schema_version":"7.09","scene_qas":[scene1,scene2],
            "lesson_qa":lesson,"course_qa":course,
            "unified_qa_gate":{"valid":valid,"status":"PASS" if valid else "BLOCKED",
                               "errors":[] if valid else ["QA_RELEASE_BLOCKED"]}}
