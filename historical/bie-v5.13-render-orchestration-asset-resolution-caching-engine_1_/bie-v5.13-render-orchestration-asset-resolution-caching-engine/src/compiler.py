from dependencies import dependency_graph
from assets import resolve_assets
from scheduler import build_render_jobs,schedule_parallel
from assembly import assembly_manifest,validate_assembly

def compile_orchestration(scenes, asset_library, cache=None,
                          renderer_version="1.0", fps=30,width=1920,height=1080):
    cache=cache or {}
    refs=[r for s in scenes for r in s.get("asset_refs",[])]
    assets=resolve_assets(refs,asset_library)
    graph=dependency_graph(scenes,asset_library)
    jobs=build_render_jobs(scenes,cache,renderer_version,asset_library)
    schedule=schedule_parallel(jobs)
    errors=[f"MISSING_ASSET:{x}" for x in assets["missing"]]
    manifest=assembly_manifest(
      [{"scene_id":s["scene_id"],"sequence_index":i,"status":"PENDING"}
       for i,s in enumerate(scenes)],fps,width,height)
    assembly=validate_assembly(manifest)
    errors+=assembly["errors"]
    return {"schema_version":"5.13","dependency_graph":graph,
            "asset_resolution":assets,"render_jobs":jobs,
            "schedule":schedule,"assembly_manifest":manifest,
            "quality_gate":{"valid":not errors,"errors":errors}}
