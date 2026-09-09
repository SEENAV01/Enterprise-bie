def ordered(events):
    return sorted(events,key=lambda e:(e["aggregate_id"],e["sequence"],e["event_id"]))

def ordering_errors(events):
    errors=[]
    groups={}
    for e in events: groups.setdefault(e["aggregate_id"],[]).append(e["sequence"])
    for agg,seqs in groups.items():
        s=sorted(seqs)
        if len(s)!=len(set(s)): errors.append(f"DUPLICATE_SEQUENCE:{agg}")
        if s and s!=list(range(min(s),max(s)+1)): errors.append(f"SEQUENCE_GAP:{agg}")
    return errors
