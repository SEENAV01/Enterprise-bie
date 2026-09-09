def timeline_policy():
    return {
      "narration_is_primary_temporal_anchor":True,
      "duration_is_content_driven":True,
      "visual_beats_are_frame_addressable":True,
      "captions_share_the_master_timeline":True,
      "audio_tracks_share_the_master_timeline":True,
      "phoneme_alignment_is_optional_but_supported":True,
      "music_can_be_ducked_under_narration":True,
      "no_artificial_lesson_duration":True
    }
