from dataclasses import dataclass
@dataclass(frozen=True)
class FormulaQA:
 passed:bool; failures:tuple[str,...]
def check_formula(formula:str,balanced:bool=True,known_symbols:set[str]|None=None,used_symbols:set[str]|None=None)->FormulaQA:
 f=[]
 if not formula.strip():f.append("empty_formula")
 if "=" not in formula and not any(x in formula for x in ("<",">","≈")):f.append("missing_relation")
 if not balanced:f.append("unbalanced_structure")
 if known_symbols is not None and used_symbols is not None:
  unknown=sorted(used_symbols-known_symbols)
  if unknown:f.append("unknown_symbols:"+",".join(unknown))
 return FormulaQA(not f,tuple(f))
