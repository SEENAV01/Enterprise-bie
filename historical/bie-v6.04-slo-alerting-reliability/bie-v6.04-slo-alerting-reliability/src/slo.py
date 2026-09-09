def slo(name,target,sli_name,
         window=None,description=None):
    return {"name":name,"target":target,
            "sli":sli_name,"window":window,
            "description":description}

def meets(slo_record,sli_value):
    return sli_value >= slo_record["target"]
