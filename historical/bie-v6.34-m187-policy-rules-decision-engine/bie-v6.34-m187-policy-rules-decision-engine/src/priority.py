def order_rules(rules):
    return sorted(rules,key=lambda r:(-r.get("priority",0),r["rule_id"]))

def highest(rules):
    ordered=order_rules(rules)
    return ordered[0] if ordered else None
