WEIGHTS={
"PRIMARY":1.00,"STANDARDS_BODY":0.98,"GOVERNMENT":0.97,
"ACADEMIC_REVIEW":0.96,"UNIVERSITY":0.92,"PROFESSIONAL_ORG":0.90,
"TEXTBOOK":0.88,"REFERENCE":0.82,"NEWS":0.70,"GENERAL_WEB":0.45
}
def rank_sources(sources):
    return sorted(sources,key=lambda s:WEIGHTS.get(s.get("source_class"),0),reverse=True)
