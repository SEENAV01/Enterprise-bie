class E(ValueError):pass
def score(frequency,structural,objective,assessment):
 vals=(frequency,structural,objective,assessment)
 if any(not 0<=x<=1 for x in vals):raise E("score")
 s=.2*frequency+.3*structural+.3*objective+.2*assessment
 return {"salience":s,"band":"CORE" if s>=.8 else ("SUPPORTING" if s>=.5 else "INCIDENTAL")}
