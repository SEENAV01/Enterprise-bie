def graph_spec(x, series, x_label="", y_label="", annotations=None):
    return {
      "type":"GRAPH",
      "x":x,
      "series":series,
      "x_label":x_label,
      "y_label":y_label,
      "annotations":annotations or [],
      "axes_required":True
    }
