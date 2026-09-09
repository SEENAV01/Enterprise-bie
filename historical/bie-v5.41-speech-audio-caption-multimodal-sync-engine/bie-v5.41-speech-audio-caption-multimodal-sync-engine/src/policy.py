def audio_sync_policy():
    return {
      "narration_is_structured":True,
      "speech_timing_can_be_actual":True,
      "word_level_alignment_is_supported":True,
      "captions_are_first_class":True,
      "audio_cues_are_explicit":True,
      "cross_modal_anchors_are_explicit":True,
      "timing_can_be_derived_from_audio":True,
      "estimated_timing_is_distinguished_from_actual_timing":True,
      "renderer_is_separate_from_audio_sync":True,
      "domain_agnostic":True
    }
