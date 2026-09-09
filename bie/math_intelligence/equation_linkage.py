from dataclasses import dataclass
import re
@dataclass(frozen=True)
class EquationLink:
 equation_id:str; symbols:tuple[str,...]; source:str
def link_equation(equation_id:str,equation:str,source:str)->EquationLink:
 if not equation_id or not source:raise ValueError("id and source required")
 symbols=tuple(sorted(set(re.findall(r"[A-Za-zα-ωΑ-Ω]+",equation or ""))))
 return EquationLink(equation_id,symbols,source)
def equations_for(symbol:str,links:list[EquationLink])->tuple[str,...]:
 return tuple(l.equation_id for l in links if symbol in l.symbols)
