import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from identity import content_id,artifact_id
from artifacts import register_artifact
from dedup import deduplicate
def test_m272():
 s={}; h=content_id(b"x"); a=artifact_id("n","a","v1")
 assert register_artifact(s,a,h)["created"]
 assert not register_artifact(s,a,h)["created"]
 assert len(deduplicate(s,h))==1
