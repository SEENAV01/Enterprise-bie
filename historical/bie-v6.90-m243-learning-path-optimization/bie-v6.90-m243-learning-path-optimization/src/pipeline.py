from path import build_learning_path

def build_learning_path_runtime():
    units=[
      {"concept_id":"c-charge","concept_ids":["c-charge"],"duration_minutes":5,
       "intrinsic_load":0.4,"extraneous_load":0.1,"germane_load":0.3,"priority":1},
      {"concept_id":"c-field","concept_ids":["c-field"],"duration_minutes":6,
       "intrinsic_load":0.5,"extraneous_load":0.1,"germane_load":0.3,"priority":2},
      {"concept_id":"c-force","concept_ids":["c-force"],"duration_minutes":7,
       "intrinsic_load":0.6,"extraneous_load":0.1,"germane_load":0.3,"priority":3}]
    prereq={"c-field":["c-charge"],"c-force":["c-field"]}
    result=build_learning_path(units,prereq)
    return {"schema_version":"6.90","learning_path":result,
            "optimization_gate":{"valid":result["valid"],"errors":[] if result["valid"] else ["PATH_QA_FAILURE"]}}
