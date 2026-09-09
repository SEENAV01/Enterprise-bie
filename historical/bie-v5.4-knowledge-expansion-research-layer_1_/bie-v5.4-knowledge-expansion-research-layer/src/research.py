def research_request(expansion, query):
    return {
      "expansion_id":expansion["expansion_id"],
      "query":query,
      "source_policy":{
        "prefer_primary":True,
        "prefer_authoritative":True,
        "date_sensitive_topics_require_recent_sources":True
      },
      "status":"PENDING_RESEARCH"
    }

def research_result(request, sources):
    return {
      **request,
      "sources":sources,
      "status":"RESEARCHED" if sources else "NO_EVIDENCE_FOUND"
    }
