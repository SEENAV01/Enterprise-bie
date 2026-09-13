def choose_depth(readiness,objective_level,source_depth):
 if readiness<.5:return "BRIDGE"
 if objective_level in {"ANALYZE","EVALUATE","CREATE"} and source_depth>=.7:return "DEEP"
 return "STANDARD"
