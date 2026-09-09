import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_audio_sync

def test_sync():
 s={"segments":[{"segment_id":"s1","text":"hello world"}]}
 a=[{"segment_id":"s1","words":[
   {"text":"hello","start":0,"end":.3},
   {"text":"world","start":.31,"end":.6}]}]
 r=compile_audio_sync(s,a)
 assert r["quality_gate"]["valid"]

def test_bad_alignment():
 s={"segments":[{"segment_id":"s1","text":"hello"}]}
 a=[{"segment_id":"s1","words":[
   {"text":"hello","start":.5,"end":.2}]}]
 assert not compile_audio_sync(s,a)["quality_gate"]["valid"]
