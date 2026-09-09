
class DiagramClassError(ValueError):pass
KINDS={"scientific_diagram","process_flow","graph_plot","map","timeline","geometry","circuit","anatomy","illustration","photo","unknown"}
def classify(scores,min_conf=.55):
 if not scores:return ("unknown",0.0)
 for k,v in scores.items():
  if k not in KINDS or not 0<=float(v)<=1:raise DiagramClassError("invalid score")
 k,v=max(scores.items(),key=lambda x:(float(x[1]),x[0]))
 return (k,float(v)) if float(v)>=min_conf else ("unknown",float(v))
