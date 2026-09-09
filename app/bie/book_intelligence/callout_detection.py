
class CalloutError(ValueError):pass
def classify(features):
 border=float(features.get("border",0));fill=float(features.get("fill",0));label=float(features.get("label",0));isolation=float(features.get("isolation",0))
 vals=(border,fill,label,isolation)
 if any(not 0<=v<=1 for v in vals):raise CalloutError("feature range")
 score=.3*border+.2*fill+.3*label+.2*isolation
 if score>=.75:return "CALLOUT_HIGH"
 if score>=.5:return "CALLOUT_POSSIBLE"
 return "MAIN_CONTENT"
