TIERS=("HOT","WARM","COLD","DEEP_ARCHIVE")

def storage_policy(tier,allowed_tiers=None):
    if tier not in TIERS: raise ValueError("INVALID_STORAGE_TIER")
    return {"tier":tier,"allowed_tiers":allowed_tiers or list(TIERS)}

def transition_tier(current,target,policy):
    if target not in policy.get("allowed_tiers",[]):
        raise ValueError("TIER_NOT_ALLOWED")
    return {"from":current,"to":target}
