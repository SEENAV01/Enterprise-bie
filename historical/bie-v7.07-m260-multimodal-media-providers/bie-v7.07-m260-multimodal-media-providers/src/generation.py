def create_generation_request(asset_id, media_kind, prompt, constraints=None):
    return {"asset_id":asset_id,"media_kind":media_kind,"prompt":prompt,
            "constraints":constraints or {},"status":"REQUESTED"}

def accept_generation(request, provider_id, output_uri, metadata=None):
    return {**request,"provider_id":provider_id,"output_uri":output_uri,
            "metadata":metadata or {},"status":"GENERATED"}
