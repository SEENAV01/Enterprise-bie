def promotion_request(artifact_id,source_zone,
                      target_zone,validation_ref=None):
    return {"artifact_id":artifact_id,
            "source_zone":source_zone,
            "target_zone":target_zone,
            "validation_ref":validation_ref}

def promotion_ready(request):
    return request.get("source_zone")=="SANDBOX" and            request.get("target_zone")=="WORKER" and            bool(request.get("validation_ref"))
