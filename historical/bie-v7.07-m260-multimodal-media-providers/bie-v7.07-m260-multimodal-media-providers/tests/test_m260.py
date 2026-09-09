import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from providers import register_provider,select_provider
from captions import align_captions,validate_captions
from quality import provider_fallback
def test_m260():
 r={}
 register_provider(r,"p1","image",["generate"],100)
 register_provider(r,"p2","image",["generate"],50)
 assert select_provider(r,"image","generate")["id"]=="p1"
 assert provider_fallback(r,"image","generate","p1")["id"]=="p2"
 c=align_captions([{"text":"Hello.","start":0,"end":1}])
 assert validate_captions(c,1.2)["valid"]
