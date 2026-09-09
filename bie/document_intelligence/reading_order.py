
class ReadingOrderError(ValueError):pass
def validate_order(region_ids,order):
 if len(order)!=len(region_ids) or set(order)!=set(region_ids) or len(set(order))!=len(order):raise ReadingOrderError("order must be exact permutation")
 return tuple(order)
def edges(order):return tuple(zip(order,order[1:]))
