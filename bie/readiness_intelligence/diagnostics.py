from dataclasses import dataclass
@dataclass(frozen=True)
class DiagnosticQuestion:
 concept:str; prompt:str; expected:str; difficulty:str
def generate_diagnostic_questions(prerequisites:dict[str,dict], max_questions:int=5)->list[DiagnosticQuestion]:
 if max_questions<1: raise ValueError("max_questions must be positive")
 out=[]
 for concept,spec in sorted(prerequisites.items(),key=lambda x:(-float(x[1].get("strength",.5)),x[0])):
  objective=spec.get("objective") or f"explain {concept}"
  expected=spec.get("expected") or objective
  kind=spec.get("kind","conceptual")
  prompt=(f"Without notes, {objective}." if kind=="conceptual" else f"Solve or demonstrate: {objective}.")
  out.append(DiagnosticQuestion(concept,prompt,expected,"core" if spec.get("strength",.5)>=.7 else "supporting"))
 return out[:max_questions]
