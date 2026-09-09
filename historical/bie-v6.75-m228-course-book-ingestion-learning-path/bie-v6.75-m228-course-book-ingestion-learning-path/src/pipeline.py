from ingestion import ingest_outline,validate_structure
from decomposition import decompose_section,lesson_units
from mapping import map_concepts_to_sections
from learning_path import build_learning_path,validate_path

def build_course_runtime():
    outline={"metadata":{"title":"Electrostatics"},
      "chapters":[
        {"chapter_id":"ch1","title":"Charge","number":1},
        {"chapter_id":"ch2","title":"Field","number":2}],
      "sections":[
        {"section_id":"s1","title":"Electric charge","chapter_id":"ch1","number":1},
        {"section_id":"s2","title":"Electric field","chapter_id":"ch2","number":1}]}
    doc=ingest_outline("book://electrostatics",outline)
    structure=validate_structure(doc)
    concepts=[
      {"concept_id":"c1","title":"Charge","section_id":"s1"},
      {"concept_id":"c2","title":"Electric field","section_id":"s2"}]
    decomposed=[decompose_section(s,[c for c in concepts if c["section_id"]==s["section_id"]])
                for s in doc["sections"]]
    lessons=[]
    for d in decomposed:
        lessons.extend(lesson_units(d["section_id"],d["concepts"],3))
    mapping=map_concepts_to_sections(concepts,doc["sections"])
    path=build_learning_path(doc["chapters"],doc["sections"],lessons,["c1","c2"])
    path_check=validate_path(path)
    return {"schema_version":"6.75","source":doc["source"],
            "structure":doc,"structure_validation":structure,
            "concepts":concepts,"decomposition":decomposed,
            "concept_mapping":mapping,"lessons":lessons,
            "learning_path":path,"learning_path_validation":path_check,
            "learning_path_gate":{"valid":structure["passed"] and
                all(x["mapped"] for x in mapping) and path_check["passed"],"errors":[]}}
