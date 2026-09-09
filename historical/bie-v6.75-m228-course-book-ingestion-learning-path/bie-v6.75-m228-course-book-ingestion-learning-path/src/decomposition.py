def decompose_section(section,concepts):
    return {"section_id":section["section_id"],
            "concepts":[{"concept_id":c["concept_id"],
                         "title":c["title"]} for c in concepts]}

def lesson_units(section_id,concepts,max_concepts=3):
    units=[]
    for i in range(0,len(concepts),max_concepts):
        units.append({"lesson_id":f"{section_id}-L{i//max_concepts+1}",
                      "section_id":section_id,
                      "concept_ids":[c["concept_id"] for c in concepts[i:i+max_concepts]]})
    return units
