import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))

from voice import voice,valid
from narration import narration_segment,ordered
from pronunciation import pronunciation
from audio_cues import cue
from audio_timeline import timeline,valid as timeline_valid
from mix import mix_profile
from evidence import evidence_binding,grounded
from provenance import provenance,traceable
from verification import verification,passed

def test_voice_and_narration():
    v=voice("v","TEACHER","en")
    n=narration_segment("n","b","Explain.",v["voice_id"],0,10)
    p=pronunciation("charge","chahrj")
    c=cue("c","MUSIC",0,10)
    tl=timeline([n],[c])
    assert valid(v) and n["voice_id"]=="v" and p["term"]=="charge"
    assert tl and timeline_valid(tl)

def test_audio_traceability():
    m=mix_profile()
    b=evidence_binding("n",["e"])
    p=provenance("a",["script"],["scene"],["e"])
    v=verification("v","a","PASS",["e"])
    assert m["master_lufs"]==-14 and grounded(b)
    assert traceable(p) and passed(v)
