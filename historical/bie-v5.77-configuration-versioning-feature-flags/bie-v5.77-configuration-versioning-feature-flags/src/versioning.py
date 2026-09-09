def version(major,minor,patch):
    return f"{major}.{minor}.{patch}"

def bump(current,kind):
    a,b,c=map(int,current.split("."))
    if kind=="major": a,b,c=a+1,0,0
    elif kind=="minor": b,c=b+1,0
    elif kind=="patch": c+=1
    else: raise ValueError("UNKNOWN_BUMP")
    return version(a,b,c)
