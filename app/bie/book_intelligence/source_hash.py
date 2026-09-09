
import hashlib
class HashError(ValueError):pass
def source_sha256(data):
 if not isinstance(data,(bytes,bytearray)) or not data:raise HashError("non-empty bytes required")
 return hashlib.sha256(bytes(data)).hexdigest()
def same_source(a,b):return source_sha256(a)==source_sha256(b)
