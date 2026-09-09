def build_render_jobs(scenes, cache, renderer_version, asset_manifest):
    jobs=[]
    for scene in scenes:
        key=__import__("cache").cache_key(scene,renderer_version,asset_manifest)
        jobs.append({
          "scene_id":scene["scene_id"],"cache_key":key,
          "status":"CACHED" if key in cache else "READY",
          "parallelizable":True
        })
    return jobs

def schedule_parallel(jobs):
    return {"batches":[[j for j in jobs if j["status"]=="READY"]],
            "cached":[j for j in jobs if j["status"]=="CACHED"]}
