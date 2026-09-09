def reassessment_decision(mastery_before,mastery_after,threshold=0.65):
    improved=mastery_after>mastery_before
    passed=mastery_after>=threshold
    return {"mastery_before":mastery_before,"mastery_after":mastery_after,
            "improved":improved,"passed":passed,
            "next_action":"PROGRESS" if passed else "REMEDIATE"}

def close_loop(decision):
    return {"closed":decision["passed"],"next_action":decision["next_action"]}
