import re
class LatexNormalizeError(ValueError): pass
def normalize(latex):
    if not isinstance(latex,str) or not latex.strip(): raise LatexNormalizeError("empty latex")
    s=latex.strip().replace("−","-").replace("×",r"\times ").replace("÷",r"\div ")
    s=re.sub(r"\s+"," ",s)
    if s.count("{")!=s.count("}") or s.count("[")!=s.count("]"): raise LatexNormalizeError("unbalanced delimiters")
    return s
