class E(ValueError):pass
def evaluate(confidences,review_threshold=.8,max_low_fraction=.1):
 if not confidences or any(not 0<=x<=1 for x in confidences):raise E("confidence")
 low=sum(x<review_threshold for x in confidences)/len(confidences)
 return {"mean":sum(confidences)/len(confidences),"low_fraction":low,"passed":low<=max_low_fraction}
