def classify_external_support(expansion, sources):
    if not sources:
        return "UNSUPPORTED"
    if expansion["kind"] in ("COUNTEREXAMPLE","LIMITATION","MODERN_CONTEXT"):
        return "EXTERNAL_EVIDENCE"
    return "EXTERNAL_OR_DERIVED"

def source_quality(source):
    authority=source.get("authority",0)
    primary=source.get("primary",False)
    recency=source.get("recency_score",0)
    return round(0.5*authority+0.3*int(primary)+0.2*recency,3)
