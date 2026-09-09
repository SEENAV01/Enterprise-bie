from dataclasses import dataclass
import ast
@dataclass(frozen=True)
class Simplification:
 valid:bool; complexity_before:int; complexity_after:int
def complexity(expr:str)->int:
 tree=ast.parse(expr.replace("^","**"),mode="eval")
 return sum(1 for n in ast.walk(tree) if isinstance(n,(ast.BinOp,ast.UnaryOp,ast.Call)))
def validate_simplification(before:str,after:str,equivalent:bool)->Simplification:
 a,b=complexity(before),complexity(after)
 return Simplification(bool(equivalent and b<=a),a,b)
