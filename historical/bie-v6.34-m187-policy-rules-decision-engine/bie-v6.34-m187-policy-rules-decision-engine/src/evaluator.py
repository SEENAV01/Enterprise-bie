def evaluate(rule, context):
    # Reference evaluator: equality predicates only.
    predicate=rule["predicate"]
    key=predicate.get("field")
    expected=predicate.get("equals")
    matched=context.get(key)==expected
    return {"rule_id":rule["rule_id"],"matched":matched,
            "effect":rule["effect"] if matched else None}

def evaluate_policy(policy, context):
    results=[evaluate(r,context) for r in policy["rules"]]
    matched=[x for x in results if x["matched"]]
    if policy["mode"]=="FIRST_MATCH":
        matched=matched[:1]
    elif policy["mode"]=="BEST_MATCH":
        matched=sorted(matched,key=lambda x: next(
            r["priority"] for r in policy["rules"] if r["rule_id"]==x["rule_id"]),reverse=True)[:1]
    return {"policy_id":policy["policy_id"],"version":policy["version"],
            "matches":matched,"decision":matched[0]["effect"] if matched else None}
