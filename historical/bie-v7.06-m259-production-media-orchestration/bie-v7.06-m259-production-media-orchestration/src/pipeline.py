from registry import register_asset,resolve_asset
from versioning import asset_fingerprint
from dedupe import deduplicate_assets
from media_graph import build_media_graph,validate_media_graph
from cache import cache_key,cache_lookup,cache_store

def build_m259_runtime():
    registry={}
    assets=[
      register_asset(registry,"diagram-field","diagram","assets/field.svg","1.0",
                     {"concept":"electric-field"}),
      register_asset(registry,"narration-1","tts","audio/n1.wav","1.0",
                     {"language":"en-IN"}),
      register_asset(registry,"captions-1","captions","captions/n1.vtt","1.0",
                     {"language":"en-IN"}),
      register_asset(registry,"image-field","image","assets/field.png","1.0",{})]
    prepared=[]
    for a in assets: prepared.append({**a,"fingerprint":asset_fingerprint(a)})
    dedupe=deduplicate_assets(prepared)
    graph=build_media_graph("scene-c-field",[
      {"id":"diagram-field","kind":"diagram","relation":"REQUIRED"},
      {"id":"narration-1","kind":"tts","relation":"REQUIRED"},
      {"id":"captions-1","kind":"captions","relation":"DERIVED_FROM"},
      {"id":"image-field","kind":"image","relation":"OPTIONAL"}])
    graph_check=validate_media_graph(graph)
    cache={}
    a=prepared[0]
    key=cache_key(a["id"],a["fingerprint"])
    before=cache_lookup(cache,key)
    stored=cache_store(cache,key,{"uri":a["uri"],"verified":True})
    after=cache_lookup(cache,key)
    resolution=resolve_asset(registry,"diagram-field","1.0")
    valid=graph_check["valid"] and bool(dedupe["unique"]) and resolution is not None and after is not None
    return {"schema_version":"7.06","registry":registry,"assets":prepared,
            "deduplication":dedupe,"media_graph":graph,"graph_validation":graph_check,
            "cache_key":key,"cache_before":before,"cache_after":after,
            "resolved_asset":resolution,
            "media_orchestration_gate":{"valid":valid,"errors":[] if valid else ["MEDIA_ORCHESTRATION_FAILURE"]}}
