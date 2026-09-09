from planning import build_content_plan
from prerequisite_generation import generate_lesson_sequence
from coverage import concept_coverage,prerequisite_coverage
from content_units import build_units
from validation import validate_plan

def build_grounded_content_planning_runtime():
    graph={"nodes":[
      {"node_id":"c-charge","node_type":"CONCEPT","label":"Electric Charge"},
      {"node_id":"c-field","node_type":"CONCEPT","label":"Electric Field"},
      {"node_id":"c-force","node_type":"CONCEPT","label":"Electric Force"}],
      "edges":[
      {"source":"c-charge","target":"c-field","relation":"PREREQUISITE"},
      {"source":"c-field","target":"c-force","relation":"PREREQUISITE"}]}
    targets=["c-force"]
    pmap={"c-field":["c-charge"],"c-force":["c-field"]}
    plan=build_content_plan(graph,targets)
    sequence=generate_lesson_sequence(targets,pmap)
    units=build_units(sequence,{n["node_id"]:n["label"] for n in graph["nodes"]})
    direct=concept_coverage(targets,sequence)
    prereq=prerequisite_coverage(targets,pmap,sequence)
    validation=validate_plan(sequence,targets,pmap)
    return {"schema_version":"6.89","content_plan":plan,
            "lesson_sequence":sequence,"lesson_units":units,
            "target_coverage":direct,"prerequisite_coverage":prereq,
            "plan_validation":validation,
            "grounded_planning_gate":{"valid":validation["passed"] and
                prereq["coverage"]>=1.0,"errors":[]}}
