from dataclasses import dataclass
@dataclass(frozen=True)
class Skill:
 id:str; children:tuple[str,...]=()
@dataclass(frozen=True)
class GranularityResult:
 requested:str; selected:tuple[str,...]; reason:str
def minimum_required_scope(requested:str, hierarchy:dict[str,Skill], required_leaves:set[str])->GranularityResult:
 if requested not in hierarchy: raise ValueError("unknown requested concept")
 def leaves(n):
  node=hierarchy[n]
  if not node.children:return {n}
  out=set()
  for c in node.children:
   if c not in hierarchy: raise ValueError("unknown child")
   out|=leaves(c)
  return out
 candidates=leaves(requested)&required_leaves
 if not candidates:return GranularityResult(requested,(), "no_required_subskill")
 if candidates==leaves(requested):return GranularityResult(requested,(requested,), "whole_concept_required")
 return GranularityResult(requested,tuple(sorted(candidates)),"minimum_subskills_only")
