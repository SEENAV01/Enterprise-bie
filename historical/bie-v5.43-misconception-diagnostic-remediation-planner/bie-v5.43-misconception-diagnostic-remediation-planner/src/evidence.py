def evidence_pattern(pattern_id,evidence_refs,signals=None,
                     supporting=None,contradicting=None):
    return {"pattern_id":pattern_id,"evidence_refs":evidence_refs,
            "signals":signals or {},"supporting":supporting or [],
            "contradicting":contradicting or []}

def confidence_from_signals(signals):
    vals=[v for v in signals.values() if isinstance(v,(int,float))]
    if not vals: return None
    return max(0.0,min(1.0,sum(vals)/len(vals)))
