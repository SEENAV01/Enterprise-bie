from dataclasses import dataclass
@dataclass(frozen=True)
class Operator: symbol:str; arity:int; precedence:int; associativity:str
OPS={"+":(2,10,"left"),"-":(2,10,"left"),"*":(2,20,"left"),"/":(2,20,"left"),"^":(2,30,"right"),"=":(2,5,"none"),"±":(2,10,"none"),"·":(2,20,"left")}
def operator_info(s):
 if s not in OPS: raise ValueError("unknown operator")
 a,p,r=OPS[s];return Operator(s,a,p,r)
