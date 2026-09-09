
class HierarchyError(ValueError):pass
def infer_level(feature,thresholds=(.9,.75,.6,.45)):
 score=float(feature.get("prominence",0))
 if not 0<=score<=1:raise HierarchyError("prominence")
 for i,t in enumerate(thresholds,1):
  if score>=t:return i
 return None
def validate_hierarchy(nodes):
 stack=[]
 for n in nodes:
  level=n.get("level")
  if level is None:continue
  if level<1:raise HierarchyError("level")
  if stack and level>stack[-1]+1:raise HierarchyError("hierarchy jump")
  while stack and stack[-1]>=level:stack.pop()
  stack.append(level)
 return True
