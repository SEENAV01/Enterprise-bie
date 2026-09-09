def temporal_policy():
    return {
      "timing_is_audio_driven":True,
      "scene_duration_can_expand_to_fit_explanation":True,
      "word_or_phrase_timing_is_explicit":True,
      "captions_derive_from_timed_narration":True,
      "visual_cues_can_anchor_to_phrases":True,
      "emphasis_events_are_explicit":True,
      "fixed_global_scene_duration_is_not_required":True,
      "audio_sync_does_not_change_domain_truth":True,
      "remotion_timeline_is_a_downstream_target":True
    }
