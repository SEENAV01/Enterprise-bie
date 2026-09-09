def coordinate_system(system_id, dimensions=2, axes=None, origin=None):
    return {
      "system_id":system_id,"dimensions":dimensions,
      "axes":axes or [],"origin":origin or [0]*dimensions
    }

def geometric_object(object_id, kind, parameters, frame="WORLD"):
    return {
      "object_id":object_id,"kind":kind,
      "parameters":parameters,"frame":frame
    }
