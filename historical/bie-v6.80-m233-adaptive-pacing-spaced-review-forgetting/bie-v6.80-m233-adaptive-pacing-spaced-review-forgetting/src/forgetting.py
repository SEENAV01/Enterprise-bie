import math

def retention(initial_mastery, days_since_review, half_life_days=7):
    decay=0.5**(days_since_review/half_life_days)
    return max(0.0,min(1.0,initial_mastery*decay))

def forgetting_risk(mastery,days_since_review,half_life_days=7):
    predicted=retention(mastery,days_since_review,half_life_days)
    risk=1-predicted
    level="LOW" if risk<0.25 else ("MEDIUM" if risk<0.5 else "HIGH")
    return {"predicted_retention":predicted,"risk":risk,"level":level}
