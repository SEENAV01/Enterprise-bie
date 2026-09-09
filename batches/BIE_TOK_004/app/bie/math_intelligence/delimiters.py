from dataclasses import dataclass
@dataclass(frozen=True)
class DelimiterResult: valid:bool; error_index:int|None; expected:str|None
PAIRS={")":"(","]":"[","}":"{"}; OPEN=set(PAIRS.values())
def validate_delimiters(s):
 stack=[]
 for i,ch in enumerate(s or ""):
  if ch in OPEN:stack.append((ch,i))
  elif ch in PAIRS:
   if not stack or stack[-1][0]!=PAIRS[ch]:return DelimiterResult(False,i, {v:k for k,v in PAIRS.items()}.get(stack[-1][0]) if stack else None)
   stack.pop()
 if stack:
  ch,i=stack[-1];return DelimiterResult(False,i,{v:k for k,v in PAIRS.items()}[ch])
 return DelimiterResult(True,None,None)
