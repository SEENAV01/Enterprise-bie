class E(ValueError):pass
def aggregate(scores):
 if not scores or any(not 0<=x<=1 for x in scores):raise E("scores")
 return sum(scores)/len(scores)
def decision(s,accept=.9,review=.7):
 if not 0<=review<=accept<=1:raise E("threshold")
 return "ACCEPT" if s>=accept else ("REVIEW" if s>=review else "REJECT")
