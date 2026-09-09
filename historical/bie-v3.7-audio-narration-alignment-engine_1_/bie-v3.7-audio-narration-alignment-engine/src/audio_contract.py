def audio_contract():
    return {
      "timing_authority":"FINAL_AUDIO",
      "word_alignment":"REQUIRED_FOR_SYNCED_ANIMATION",
      "phoneme_alignment":"OPTIONAL_HIGH_PRECISION",
      "tts_provider":"PLUGGABLE",
      "voice_change_requires_realignment":True,
      "manual_anchor_override":"SUPPORTED",
      "scene_duration":"LAST_AUDIO_EVENT_OR_NARRATION_END"
    }
