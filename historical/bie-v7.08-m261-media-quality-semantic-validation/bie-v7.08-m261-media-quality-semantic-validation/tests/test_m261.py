import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from diagram import validate_diagram
from audio import validate_audio
from captions import validate_caption_sync
def test_m261():
 assert validate_diagram({"nodes":[{"id":"a","label":"A"}],"edges":[]})["valid"]
 assert validate_audio({"uri":"x","duration_seconds":3,"lufs":-18,"clipping":False},3)["valid"]
 assert validate_caption_sync([{"start":0,"end":1,"text":"Hi"}],1.1)["valid"]
