from sync import synchronize
from quality import sync_quality
from audio_contract import audio_track_spec,speech_metadata

def compile_audio_lesson(segments,cues,voice_id="default",
                         language="en",fps=30,words_per_minute=145):
    timeline=synchronize(segments,cues,fps,words_per_minute)
    return {
      "schema_version":"5.7",
      "audio_track":audio_track_spec(voice_id,48000,2,language),
      "speech":speech_metadata(" ".join(s["text"] for s in segments),language),
      "timeline":timeline,
      "quality_gate":sync_quality(timeline)
    }
