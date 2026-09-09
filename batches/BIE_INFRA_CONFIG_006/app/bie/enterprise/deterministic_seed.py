
import hashlib, random
class SeedError(ValueError): pass
def derive_seed(run_id:str, stage_id:str, config_hash:str)->int:
    if not run_id or not stage_id or len(config_hash)!=64: raise SeedError("run_id, stage_id and sha256 config hash required")
    d=hashlib.sha256(f"{run_id}|{stage_id}|{config_hash}".encode()).digest()
    return int.from_bytes(d[:8],"big",signed=False)
def seeded_rng(run_id,stage_id,config_hash):
    return random.Random(derive_seed(run_id,stage_id,config_hash))
def deterministic_choice(items,run_id,stage_id,config_hash):
    if not items: raise SeedError("items required")
    return seeded_rng(run_id,stage_id,config_hash).choice(list(items))
