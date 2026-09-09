def text_spec(text, role="body", max_lines=3, emphasis=None):
    return {
      "type":"TEXT",
      "text":text,
      "role":role,
      "max_lines":max_lines,
      "emphasis":emphasis or [],
      "safe_area":True
    }
