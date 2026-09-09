def map_concepts_to_sections(concepts,sections):
    ids={s["section_id"] for s in sections}
    return [{"concept_id":c["concept_id"],
             "section_id":c["section_id"],
             "mapped":c["section_id"] in ids} for c in concepts]
