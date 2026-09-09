def graph(graph_id, x_label, y_label, domain,
          function=None, data=None):
    return {
      "graph_id":graph_id,"x_label":x_label,"y_label":y_label,
      "domain":domain,"function":function,"data":data
    }

def graph_animation(graph_id, parameter, values):
    return {
      "graph_id":graph_id,"parameter":parameter,
      "values":values,
      "animation_semantics":"parameter_sweep"
    }
