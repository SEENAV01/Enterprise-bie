import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_temporal_scene

def test_audio_driven():
 r=compile_temporal_scene("s",10.0,
  [{"phrase_id":"p","text":"Hello","start":0,"end":2}],
  [{"cue_id":"c","target_id":"x","trigger_type":"START","phrase_ref":"p"}],
  "audio.wav")
 assert r["quality_gate"]["valid"]
 assert r["timeline"]["timing_policy"]=="AUDIO_DRIVEN"
 assert r["visual_cues"][0]["start"]==0

def test_phrase_overrun():
 r=compile_temporal_scene("s",2.0,
  [{"phrase_id":"p","text":"Too long","start":0,"end":3}],[])
 assert not r["quality_gate"]["valid"]
