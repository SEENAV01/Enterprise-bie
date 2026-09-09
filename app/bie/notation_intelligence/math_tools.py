from dataclasses import dataclass
@dataclass(frozen=True)
class MathToolRequirement:
 tool:str; confidence:float; evidence:tuple[str,...]
RULES={
 "algebra":{"solve","equation","rearrange","unknown"},
 "vectors":{"vector","magnitude","direction","component"},
 "calculus":{"derivative","differentiate","integral","integrate","rate of change"},
 "trigonometry":{"sine","cosine","tan","angle"},
 "graphing":{"plot","graph","slope","axis"},
 "statistics":{"mean","median","variance","probability"},
}
def infer_math_tools(text:str)->list[MathToolRequirement]:
 low=(text or "").casefold();out=[]
 for tool,terms in RULES.items():
  hits=tuple(sorted(t for t in terms if t in low))
  if hits: out.append(MathToolRequirement(tool,round(min(.95,.45+.12*len(hits)),6),hits))
 return sorted(out,key=lambda x:(-x.confidence,x.tool))
