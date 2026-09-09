def evaluate(rules,context,
             default="DENY"):
    matched=[r for r in rules if
             r.get("condition")==context]
    if not matched:
        return {"decision":default,"matched_rules":[]}
    ordered=sorted(matched,
                   key=lambda r:r.get("priority",0),
                   reverse=True)
    return {"decision":ordered[0]["effect"],
            "matched_rules":[r["rule_id"]
                             for r in ordered]}

def validate_decision(decision):
    return decision in {"ALLOW","DENY","SET","UNSET"}
