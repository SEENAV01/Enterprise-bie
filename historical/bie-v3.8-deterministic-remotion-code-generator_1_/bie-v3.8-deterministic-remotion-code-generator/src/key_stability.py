import hashlib

def stable_key(scene_id, semantic_id):
    raw=f"{scene_id}::{semantic_id}".encode()
    return hashlib.sha1(raw).hexdigest()[:16]

def assign_stable_keys(ir):
    for i,layer in enumerate(ir.get("layers",[])):
        layer["key"]=stable_key(ir["scene_id"],layer.get("key",str(i)))
    return ir
