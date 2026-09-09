def quality_gate(media, requirements):
    errors=[]
    if not media.get("output_uri"): errors.append("MEDIA_OUTPUT_MISSING")
    if media.get("media_kind")!=requirements.get("media_kind"): errors.append("MEDIA_KIND_MISMATCH")
    for key,value in requirements.get("metadata",{}).items():
        if media.get("metadata",{}).get(key)!=value: errors.append(f"METADATA_MISMATCH:{key}")
    return {"valid":not errors,"errors":errors}

def provider_fallback(registry, media_kind, capability, failed_provider):
    candidates=[p for p in registry.values()
                if p["media_kind"]==media_kind and capability in p["capabilities"]
                and p["id"]!=failed_provider]
    return sorted(candidates,key=lambda p:-p["priority"])[0] if candidates else None
