from dataclasses import dataclass
@dataclass(frozen=True)
class SymbolicQA:
 passed:bool; failures:tuple[str,...]
def assess_symbolic(defined:set[str],used:set[str],equivalent:bool,scope_conflicts:tuple=())->SymbolicQA:
 f=[]
 unknown=sorted(used-defined)
 if unknown:f.append("undefined_symbols:"+",".join(unknown))
 if not equivalent:f.append("symbolic_non_equivalence")
 if scope_conflicts:f.append("symbol_scope_conflict")
 return SymbolicQA(not f,tuple(f))
