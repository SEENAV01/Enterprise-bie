def read_write_set(reads=None, writes=None):
    return {"reads":reads or [],"writes":writes or []}

def overlaps(a,b):
    return bool(set(a["writes"]) & (set(b["reads"]) | set(b["writes"])))
