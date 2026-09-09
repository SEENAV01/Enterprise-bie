
class ParagraphError(ValueError):pass
def group_lines(lines,max_gap=1.5,indent_tolerance=.08):
 if max_gap<=0 or not 0<=indent_tolerance<=1:raise ParagraphError("params")
 if not lines:return ()
 out=[];cur=[lines[0]]
 for prev,line in zip(lines,lines[1:]):
  gap=float(line["top"])-float(prev["bottom"])
  indent=abs(float(line.get("indent",0))-float(prev.get("indent",0)))
  if gap>max_gap or indent>indent_tolerance:
   out.append(tuple(cur));cur=[]
  cur.append(line)
 if cur:out.append(tuple(cur))
 return tuple(out)
