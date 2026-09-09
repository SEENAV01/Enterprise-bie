def invalidate(decisions,changed):
 c=set(changed)
 return tuple((i,not bool(c.intersection(e))) for i,e in decisions)
