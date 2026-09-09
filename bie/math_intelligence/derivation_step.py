from dataclasses import dataclass
@dataclass(frozen=True)
class DerivationStep:
 before:str; after:str; rule:str; justification:str; source:str|None=None
def make_step(before:str,after:str,rule:str,justification:str,source=None)->DerivationStep:
 if not all((before.strip(),after.strip(),rule.strip(),justification.strip())):raise ValueError("complete derivation evidence required")
 if before.strip()==after.strip():raise ValueError("step must transform expression")
 return DerivationStep(before.strip(),after.strip(),rule.strip(),justification.strip(),source)
