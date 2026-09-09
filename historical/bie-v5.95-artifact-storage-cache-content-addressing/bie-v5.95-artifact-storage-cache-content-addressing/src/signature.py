import hashlib

def reference_signature(content_id,signing_key_id):
    return hashlib.sha256(
        (content_id+"|"+signing_key_id).encode()
    ).hexdigest()

def verify_reference(content_id,signing_key_id,signature):
    return reference_signature(content_id,signing_key_id)==signature
