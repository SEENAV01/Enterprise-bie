from transcript import normalize_transcript
from cue_extractor import extract_cues
from audio_duration import resolve_duration
from event_mapper import map_events
from scene_boundaries import build_boundaries
from timeline import compile_timeline
from timeline_validator import validate

def compile_audio_timeline(audio, narrative_events, fps=30):
    tr=normalize_transcript(audio)
    cues=extract_cues(tr)
    duration=resolve_duration(tr)
    mapped=map_events(narrative_events,cues)
    scenes=build_boundaries(mapped,duration)
    timeline=compile_timeline(duration,fps,mapped,scenes)
    timeline["source_events"]=mapped
    timeline["audio_cues"]=cues
    timeline["validation"]=validate(timeline)
    timeline["policy"]={
      "audio_is_temporal_source_of_truth":True,
      "fixed_concept_duration":False,
      "renderer_neutral":True
    }
    return timeline
