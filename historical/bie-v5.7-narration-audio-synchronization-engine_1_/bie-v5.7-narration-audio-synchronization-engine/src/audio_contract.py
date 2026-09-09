def audio_track_spec(voice_id, sample_rate=48000, channels=2,
                     language="en"):
    return {
      "voice_id":voice_id,
      "sample_rate":sample_rate,
      "channels":channels,
      "language":language,
      "sync_reference":"semantic_timeline"
    }

def speech_metadata(text, language="en"):
    return {
      "text":text,
      "language":language,
      "requires_timestamps":True,
      "requires_word_or_phrase_alignment":True
    }
