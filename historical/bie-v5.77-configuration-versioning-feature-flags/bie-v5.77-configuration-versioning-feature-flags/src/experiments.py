import hashlib

def assignment(experiment_id,subject_id,buckets=100):
    raw=f"{experiment_id}:{subject_id}".encode()
    n=int(hashlib.sha256(raw).hexdigest(),16)%buckets
    return {"experiment_id":experiment_id,
            "subject_id":subject_id,"bucket":n}

def variant(assign,variants):
    if not variants: raise ValueError("NO_VARIANTS")
    return variants[assign["bucket"]%len(variants)]
