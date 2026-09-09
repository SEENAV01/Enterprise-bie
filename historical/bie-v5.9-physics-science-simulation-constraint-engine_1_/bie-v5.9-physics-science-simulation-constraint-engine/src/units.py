BASE={"m":(1,0),"s":(0,1),"kg":(0,0),"A":(0,0)}
def dimension(exponents=None):
    return {"exponents":exponents or {}, "normalized":True}

def quantity(value,unit,dimension_vector=None):
    return {"value":value,"unit":unit,"dimension":dimension(dimension_vector)}

def same_dimension(a,b):
    return a.get("dimension",{}).get("exponents")==b.get("dimension",{}).get("exponents")
