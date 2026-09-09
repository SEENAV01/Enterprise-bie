from dataclasses import dataclass
import ast
@dataclass(frozen=True)
class Equivalence:
 equivalent:bool; evidence:tuple[str,...]
def _eval(expr,env):
 tree=ast.parse(expr.replace("^","**"),mode="eval")
 allowed=(ast.Expression,ast.BinOp,ast.UnaryOp,ast.Add,ast.Sub,ast.Mult,ast.Div,ast.Pow,ast.USub,ast.UAdd,ast.Load,ast.Name,ast.Constant)
 if any(not isinstance(n,allowed) for n in ast.walk(tree)):raise ValueError("unsupported expression")
 return eval(compile(tree,"<math>","eval"),{"__builtins__":{}},env)
def equivalent(a:str,b:str,variables:tuple[str,...]=("x",))->Equivalence:
 probes=(-2.,-.5,1.,3.)
 evidence=[]
 for p in probes:
  env={v:p+(i*.37) for i,v in enumerate(variables)}
  try:x,y=_eval(a,env),_eval(b,env)
  except ZeroDivisionError:continue
  if abs(x-y)>1e-9:return Equivalence(False,tuple(evidence+[f"counterexample:{env}"]))
  evidence.append(f"probe:{env}")
 return Equivalence(bool(evidence),tuple(evidence))
