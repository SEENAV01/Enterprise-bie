
import json, hashlib
class ConfigHashError(ValueError): pass
def canonical_bytes(config:dict)->bytes:
    if not isinstance(config,dict): raise ConfigHashError("config must be dict")
    return json.dumps(config,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")
def config_hash(config:dict)->str:
    return hashlib.sha256(canonical_bytes(config)).hexdigest()
def verify_hash(config:dict, expected:str)->bool:
    if len(expected)!=64: raise ConfigHashError("expected sha256 hex")
    return config_hash(config)==expected.lower()
