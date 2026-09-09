
import hashlib, json, platform, sys
class FingerprintError(ValueError): pass
def build_environment_fingerprint(extra:dict|None=None)->dict:
    fp={
      "python_version": platform.python_version(),
      "implementation": platform.python_implementation(),
      "platform": platform.platform(),
      "machine": platform.machine(),
    }
    if extra:
      for k,v in extra.items():
        if not isinstance(k,str): raise FingerprintError("extra keys must be strings")
        fp[k]=str(v)
    return fp
def fingerprint_hash(fp:dict)->str:
    if not fp: raise FingerprintError("fingerprint required")
    b=json.dumps(fp,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(b).hexdigest()
