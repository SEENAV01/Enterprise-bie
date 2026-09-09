from preferences import learner_preferences,validate_preferences
from accessibility import accessibility_profile,accessibility_requirements
from policies import personalization_policy
from delivery import select_delivery
from visual import visual_constraints,narration_constraints

def build_personalization_runtime():
    pref=learner_preferences("learner-001","hi","adaptive","low",True)
    acc=accessibility_profile(captions=True,high_contrast=True,reduced_motion=True)
    policy=personalization_policy(pref,acc)
    delivery=select_delivery(policy,["VIDEO","CAPTIONED_VIDEO","TEXT"])
    return {"schema_version":"6.81","preferences":pref,"accessibility":acc,
            "requirements":accessibility_requirements(acc),"policy":policy,
            "delivery":delivery,"visual_constraints":visual_constraints(policy),
            "narration_constraints":narration_constraints(policy),
            "personalization_gate":{"valid":validate_preferences(pref) and
                bool(delivery["selected"]) and
                all(r in policy or r=="CAPTIONS" for r in []) ,"errors":[]}}
