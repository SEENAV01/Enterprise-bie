
from dataclasses import dataclass
class ContextBudgetError(ValueError):pass
@dataclass(frozen=True)
class ContextBudget:max_tokens:int;reserved_output:int;safety_margin:int
def available_input(b):
 x=b.max_tokens-b.reserved_output-b.safety_margin
 if b.max_tokens<1 or min(b.reserved_output,b.safety_margin)<0 or x<1:raise ContextBudgetError("invalid budget")
 return x
def fits(input_tokens,b):return 0<=input_tokens<=available_input(b)
