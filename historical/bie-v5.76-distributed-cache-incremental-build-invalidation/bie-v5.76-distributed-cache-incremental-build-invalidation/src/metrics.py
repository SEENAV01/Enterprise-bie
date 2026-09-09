def cache_metrics(hits,misses,rebuilds):
    total=hits+misses
    return {"hits":hits,"misses":misses,"rebuilds":rebuilds,
            "hit_rate":(hits/total if total else 0.0)}
