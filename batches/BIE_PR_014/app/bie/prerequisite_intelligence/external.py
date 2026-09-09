from dataclasses import dataclass
@dataclass(frozen=True)
class ExternalPrerequisite:
 id:str; external:bool; reason:str
def classify_external(prerequisites:set[str], corpus_concepts:set[str], aliases:dict[str,str]|None=None)->list[ExternalPrerequisite]:
 aliases=aliases or {}; canonical={aliases.get(x,x) for x in corpus_concepts}
 out=[]
 for p in sorted(prerequisites):
  cp=aliases.get(p,p); ext=cp not in canonical
  out.append(ExternalPrerequisite(p,ext,"not_in_corpus" if ext else "resolved_in_corpus"))
 return out
