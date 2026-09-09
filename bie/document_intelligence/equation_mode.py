class EquationModeError(ValueError): pass
def classify(features):
    line_fraction=float(features.get("line_fraction",0)); isolated=bool(features.get("isolated",False)); centered=bool(features.get("centered",False))
    if not 0<=line_fraction<=1: raise EquationModeError("line_fraction")
    if isolated or centered or line_fraction>=.6: return "DISPLAY"
    return "INLINE"
