def decide(equivalent,rule_known,assumptions_resolved,source):
 if not source.strip():raise ValueError("provenance required")
 f=[]
 if not equivalent:f.append("non_equivalent")
 if not rule_known:f.append("unknown_rule")
 if not assumptions_resolved:f.append("unresolved_assumptions")
 return not f,tuple(f)
