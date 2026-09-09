class E(ValueError):pass
def rank(items):
 if any("salience" not in x or not 0<=x["salience"]<=1 for x in items):raise E("salience")
 return tuple(sorted(items,key=lambda x:(-x["salience"],x["concept_id"])))
