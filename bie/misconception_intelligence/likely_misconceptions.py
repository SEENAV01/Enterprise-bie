from dataclasses import dataclass
@dataclass(frozen=True)
class LikelyMisconception:
 concept:str; misconception:str; confidence:float; reason:str
def infer_likely_misconceptions(concept:str, correct_features:set[str], distractors:dict[str,set[str]])->list[LikelyMisconception]:
 if not concept: raise ValueError("concept required")
 out=[]
 for label,features in distractors.items():
  overlap=len(correct_features & features)
  conflict=len(features-correct_features)
  if overlap and conflict:
   conf=round(min(.9,.35+.15*overlap+.1*conflict),6)
   out.append(LikelyMisconception(concept,label,conf,"partial_feature_match_with_conflict"))
 return sorted(out,key=lambda x:(-x.confidence,x.misconception))
