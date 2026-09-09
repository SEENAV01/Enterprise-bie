def encryption_metadata(algorithm,key_id,
                        key_version,mode=None):
    return {"algorithm":algorithm,
            "key_id":key_id,
            "key_version":key_version,
            "mode":mode}

def signing_metadata(algorithm,key_id,
                     key_version):
    return {"algorithm":algorithm,
            "key_id":key_id,
            "key_version":key_version,
            "purpose":"SIGN"}

def verification_contract(signature,
                          payload_digest,
                          key_reference):
    return {"signature":signature,
            "payload_digest":payload_digest,
            "key_reference":key_reference}
