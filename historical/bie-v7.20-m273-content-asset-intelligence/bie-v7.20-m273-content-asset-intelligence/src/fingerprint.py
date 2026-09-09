import hashlib

def perceptual_fingerprint(features):
    canonical="|".join(str(x) for x in features)
    return hashlib.sha256(canonical.encode()).hexdigest()[:32]

def similarity(fp_a, fp_b):
    if fp_a==fp_b:return 1.0
    matches=sum(a==b for a,b in zip(fp_a,fp_b))
    return matches/max(len(fp_a),len(fp_b),1)

def near_duplicate(fp_a, fp_b, threshold=0.90):
    return similarity(fp_a,fp_b)>=threshold
