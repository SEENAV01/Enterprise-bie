def slo(name,sli,target,window="30d"):
    return {"name":name,"sli":sli,"target":target,
            "window":window}

def meets_slo(sli_value,target):
    return sli_value>=target

def error_budget(target):
    return max(0.0,1-target)
