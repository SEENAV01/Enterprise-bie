def feedback_rule(rule_id,trigger,condition,response,
                  misconception_ref=None):
    return {"rule_id":rule_id,"trigger":trigger,"condition":condition,
            "response":response,"misconception_ref":misconception_ref}

def feedback_policy():
    return {"immediate_feedback_supported":True,
            "misconception_targeted_feedback_supported":True,
            "feedback_can_trigger_adaptation":True}
