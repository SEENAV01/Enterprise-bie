import hashlib, json

def fingerprint_scene(scene_dsl, audio_alignment=None, asset_manifest=None):
    payload={
      "scene":scene_dsl,
      "audio":audio_alignment or {},
      "assets":asset_manifest or {}
    }
    raw=json.dumps(payload,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

def build_manifest(scenes, audio_alignment, assets):
    return {
      "manifest_version":"1.0",
      "scenes":[
        {"scene_id":s["scene_id"],
         "fingerprint":fingerprint_scene(s,audio_alignment,assets)}
        for s in scenes
      ]
    }
