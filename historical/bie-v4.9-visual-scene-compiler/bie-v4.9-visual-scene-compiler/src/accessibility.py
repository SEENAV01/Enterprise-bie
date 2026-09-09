def check_text(text, max_chars=120):
    return {
      "ok":len(text or "")<=max_chars,
      "needs_split":len(text or "")>max_chars
    }

def accessibility_spec():
    return {
      "captions":True,
      "equation_alt_text":True,
      "diagram_descriptions":True,
      "safe_text_area":True,
      "contrast_check":True
    }
