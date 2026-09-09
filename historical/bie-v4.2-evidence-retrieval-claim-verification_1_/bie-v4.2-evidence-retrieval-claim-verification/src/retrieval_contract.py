def retrieval_request(item):
    return {
      "knowledge_id":item["id"],
      "query":item["title"]+" "+item.get("content",""),
      "source_preferences":[
        "PRIMARY","STANDARDS_BODY","GOVERNMENT","ACADEMIC_REVIEW",
        "UNIVERSITY","PROFESSIONAL_ORG","TEXTBOOK","REFERENCE"
      ],
      "avoid_as_sole_support":["GENERAL_WEB","UNVERIFIED_AI_OUTPUT"],
      "need_claim_level_support":True,
      "need_locator":True,
      "need_publication_or_version":True
    }
