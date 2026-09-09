def evidence_packet(item_id,artifact,
                    evaluations=None,checks=None,
                    provenance=None):
    return {"item_id":item_id,"artifact":artifact,
            "evaluations":evaluations or [],
            "checks":checks or [],
            "provenance":provenance or {}}

def summarize(packet):
    return {"item_id":packet["item_id"],
            "evaluation_count":len(packet["evaluations"]),
            "check_count":len(packet["checks"]),
            "has_provenance":bool(packet["provenance"])}
