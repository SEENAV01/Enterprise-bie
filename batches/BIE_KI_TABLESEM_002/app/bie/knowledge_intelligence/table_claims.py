class E(ValueError):pass
def claim(table,row,col,predicate,value,anchor):
 if not table or row<0 or col<0 or not predicate or value is None or not anchor:raise E("cell claim")
 return {"table_id":table,"cell":(row,col),"predicate":predicate,"value":value,"anchor_id":anchor}
