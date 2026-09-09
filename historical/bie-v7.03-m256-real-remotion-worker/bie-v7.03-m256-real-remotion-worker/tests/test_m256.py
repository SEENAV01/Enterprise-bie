import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from worker import create_worker_run,ingest_event,validate_worker_run
def test_m256():
 j={"composition_id":"s","output":"x.mp4"}
 r=create_worker_run(j,"p")
 ingest_event(r,{"kind":"progress","frame":5,"total_frames":10})
 assert r["progress"]["percent"]==50
 ingest_event(r,{"kind":"completed","output":"x.mp4","duration_frames":10})
 assert r["status"]=="SUCCEEDED"
 assert validate_worker_run(r)["valid"]
