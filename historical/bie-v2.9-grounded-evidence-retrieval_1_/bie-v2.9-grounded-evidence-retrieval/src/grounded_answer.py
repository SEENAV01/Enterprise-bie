def grounded_packet(query, ranked, context):
    return {
        "query":query,
        "evidence":ranked,
        "context":context,
        "grounding_policy":{
            "answer_only_from_retrieved_evidence":True,
            "preserve_source_terminology":True,
            "preserve_provenance":True,
            "unsupported_claims":"FLAG"
        }
    }

def unsupported_flag(answer, evidence):
    source_text=" ".join(x.get("content","") for x in evidence).lower()
    words=set(answer.lower().split())
    return [w for w in words if len(w)>5 and w not in source_text]
