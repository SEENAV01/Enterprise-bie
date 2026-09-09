def validate_temporal(cause_time,effect_time,lag_min=0,lag_max=None):
 if lag_min<0 or (lag_max is not None and lag_max<lag_min):raise ValueError("invalid lag")
 lag=effect_time-cause_time
 valid=lag>=lag_min and (lag_max is None or lag<=lag_max)
 return {"valid":valid,"lag":lag,"reason":"temporally_plausible" if valid else "temporal_violation"}
