
from collections import Counter
class HeaderFooterError(ValueError):pass
def recurring_candidates(pages,min_fraction=.6):
 if not pages or not 0<min_fraction<=1:raise HeaderFooterError("invalid input")
 counts=Counter()
 for p in pages:
  for text,pos in set(p): 
   if pos in {"top","bottom"} and text.strip():counts[(text.strip(),pos)]+=1
 threshold=len(pages)*min_fraction
 return tuple(sorted(k for k,v in counts.items() if v>=threshold))
