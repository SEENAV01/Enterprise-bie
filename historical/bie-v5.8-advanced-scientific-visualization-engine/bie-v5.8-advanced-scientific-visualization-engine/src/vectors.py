def vector(vector_id, components, coordinate_system):
    return {
      "vector_id":vector_id,"components":components,
      "coordinate_system":coordinate_system
    }

def vector_operation(op_id, operation, inputs, output):
    return {
      "op_id":op_id,"operation":operation,
      "inputs":inputs,"output":output
    }
