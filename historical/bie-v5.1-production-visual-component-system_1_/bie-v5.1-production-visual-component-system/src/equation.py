def equation_spec(expression, reveal_parts=None, highlight_parts=None):
    return {
      "type":"EQUATION",
      "expression":expression,
      "reveal_parts":reveal_parts or [],
      "highlight_parts":highlight_parts or [],
      "render":"math",
      "accessibility":{"alt_text":expression}
    }
