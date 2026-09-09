class E(ValueError):pass
def audit(source,represented,critical=()):
 s=set(source);r=set(represented);c=set(critical)
 if not c<=s:raise E("critical")
 lost=s-r;extra=r-s
 coverage=1 if not s else len(s&r)/len(s)
 return {"coverage":coverage,"lost":tuple(sorted(lost)),"extra":tuple(sorted(extra)),"passed":not(lost&c) and coverage>=.99}
