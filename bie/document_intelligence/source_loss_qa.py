class E(ValueError):pass
def evaluate(source_units,represented_units,critical_units=()):
 s=set(source_units);r=set(represented_units);c=set(critical_units)
 if not c<=s:raise E("critical not source")
 lost=s-r;critical_lost=lost&c
 coverage=1.0 if not s else len(s& r)/len(s)
 return {"passed":not critical_lost and coverage>=.98,"coverage":coverage,"lost":tuple(sorted(lost)),"critical_lost":tuple(sorted(critical_lost))}
