def process_spec(steps, current_step=None, direction="LR"):
    return {
      "type":"PROCESS",
      "steps":steps,
      "current_step":current_step,
      "direction":direction,
      "semantic_order":True
    }
