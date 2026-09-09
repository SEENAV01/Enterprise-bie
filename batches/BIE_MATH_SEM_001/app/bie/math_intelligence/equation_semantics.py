from dataclasses import dataclass
@dataclass(frozen=True)
class EquationSemantics:
 dependent:tuple[str,...]; independent:tuple[str,...]; constants:tuple[str,...]; relation_type:str
def infer_semantics(lhs:list[str],rhs:list[str],constants:set[str]=frozenset(),relation="="):
 if not lhs or not rhs:raise ValueError("both equation sides required")
 dep=tuple(x for x in lhs if x not in constants)
 const=tuple(sorted((set(lhs)|set(rhs)) & set(constants)))
 indep=tuple(sorted(set(rhs)-set(dep)-set(constants)))
 typ="equality" if relation=="=" else "inequality" if relation in {"<",">","<=",">="} else "relation"
 return EquationSemantics(tuple(dep),indep,const,typ)
