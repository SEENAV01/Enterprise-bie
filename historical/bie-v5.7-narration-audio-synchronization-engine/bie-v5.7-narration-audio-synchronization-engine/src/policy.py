def audio_sync_policy():
    return {
      "duration_is_content_driven":True,
      "no_fixed_lesson_runtime":True,
      "semantic_timing_over_uniform_timing":True,
      "visual_events_sync_to_speech":True,
      "pauses_may_expand_for_comprehension":True,
      "word_or_phrase_alignment_preferred":True
    }
