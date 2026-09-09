def decide(severity,likelihood,evidence_ids,threshold=.45):
 if not evidence_ids:raise ValueError("evidence required")
 if any(v<0 or v>1 for v in (severity,likelihood)):raise ValueError("normalized scores")
 p=.6*severity+.4*likelihood
 return p>=threshold,p,"explicit_confrontation" if p>=.7 else "diagnostic_check" if p>=threshold else "monitor"
