class E(ValueError):pass
def evaluate(expected,represented,critical=()):
 e=set(expected);r=set(represented);c=set(critical)
 if not c<=e:raise E("critical")
 coverage=1 if not e else len(e&r)/len(e)
 missing=e-r
 return {"coverage":coverage,"missing":tuple(sorted(missing)),"passed":coverage>=.95 and not(missing&c)}
