LEVELS=("REMEMBER","UNDERSTAND","APPLY","ANALYZE","EVALUATE","CREATE")
def taxonomy_rank(level):
 if level not in LEVELS: raise ValueError("unknown level")
 return LEVELS.index(level)
