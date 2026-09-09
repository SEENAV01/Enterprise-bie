import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from content_address import content_id,verify_content
from cache import cache_key,cache_entry,cache_hit
from dedup import dedup_index,register,duplicates
from transfer import transfer,complete_transfer
from integrity import integrity_check

def test_content_id():
 cid=content_id(b"hello")
 assert verify_content(b"hello",cid)

def test_cache():
 k=cache_key("render",[{"id":"a"}],{"v":1})
 assert cache_hit(cache_entry(k,"sha256:x",1))

def test_dedup():
 idx=register(dedup_index(),"c","a")
 idx=register(idx,"c","b")
 assert duplicates(idx,"c")==["a","b"]

def test_transfer():
 t=transfer("t","c","a","b",10)
 assert complete_transfer(t,True)["status"]=="COMPLETE"

def test_integrity():
 cid=content_id("x")
 assert integrity_check("x",cid)["valid"]
