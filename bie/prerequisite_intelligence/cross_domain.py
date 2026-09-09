from dataclasses import dataclass
@dataclass(frozen=True)
class CrossDomainPrerequisite:
 concept:str; domain:str; evidence:tuple[str,...]; confidence:float
RULES={
 "algebra":{"solve equation","rearrange","unknown variable"},
 "trigonometry":{"sine","cosine","tangent","angle component"},
 "calculus":{"derivative","integral","rate of change"},
 "vectors":{"vector","component","magnitude and direction"},
 "statistics":{"probability","variance","mean distribution"},
}
def detect_cross_domain(text:str,target_domain:str)->list[CrossDomainPrerequisite]:
 low=(text or "").casefold();out=[]
 for domain,terms in RULES.items():
  if domain==target_domain.casefold(): continue
  hits=tuple(sorted(t for t in terms if t in low))
  if hits: out.append(CrossDomainPrerequisite(domain,domain,hits,round(min(.95,.5+.12*len(hits)),6)))
 return sorted(out,key=lambda x:(-x.confidence,x.domain))
