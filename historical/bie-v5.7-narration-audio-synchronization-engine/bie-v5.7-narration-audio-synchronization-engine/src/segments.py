def semantic_segment(segment_id, text, purpose, visual_ids=None):
    return {
      "segment_id":segment_id,
      "text":text,
      "purpose":purpose,
      "visual_ids":visual_ids or [],
      "timing":{"start_frame":None,"end_frame":None}
    }

def segment_lesson(text_blocks):
    return [
      semantic_segment(f"seg_{i+1}",b["text"],b.get("purpose","EXPLAIN"),
                       b.get("visual_ids",[]))
      for i,b in enumerate(text_blocks)
    ]
