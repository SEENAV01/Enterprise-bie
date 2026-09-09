class E(ValueError):pass
def evaluate(expected_ids,observed_order):
 if len(set(expected_ids))!=len(expected_ids):raise E("duplicate expected")
 missing=tuple(x for x in expected_ids if x not in observed_order)
 extra=tuple(x for x in observed_order if x not in expected_ids)
 duplicates=len(observed_order)!=len(set(observed_order))
 return {"passed":not missing and not extra and not duplicates,"missing":missing,"extra":extra,"duplicates":duplicates}
