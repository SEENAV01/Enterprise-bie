def field(field_id, field_type, domain, rule, units=None):
    return {
      "field_id":field_id,"field_type":field_type,
      "domain":domain,"rule":rule,"units":units
    }

def field_visualization(field_id, representation,
                        sampling=None, normalization=None):
    return {
      "field_id":field_id,"representation":representation,
      "sampling":sampling,"normalization":normalization
    }
