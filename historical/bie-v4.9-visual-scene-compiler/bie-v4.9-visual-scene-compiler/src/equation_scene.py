def equation_object(equation,parts=None):
    return {
      "kind":"EQUATION","content":equation,
      "parts":parts or [],
      "rendering":"MATH_LAYOUT",
      "reveal_strategy":"BY_NARRATION_CUE"
    }
