def checksum(algorithm="SHA256",
             digest=None):
    if algorithm not in {"MD5","SHA256","SHA512"}:
        raise ValueError("INVALID_CHECKSUM_ALGORITHM")
    return {"algorithm":algorithm,
            "digest":digest}

def verified(record,digest):
    return record["digest"] is None or record["digest"]==digest
