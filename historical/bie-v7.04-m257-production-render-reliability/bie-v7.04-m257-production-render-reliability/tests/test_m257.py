import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from queue import create_job,enqueue
from scheduler import schedule
from checkpoint import save_checkpoint,resume_command
from retry import retry_job
from cache import cache_key,store,lookup
def test_m257():
 q=enqueue([],create_job("a",{"resources":{"cpu":1,"ram_mb":100}}))
 p=schedule(q,{"cpu":2,"ram_mb":200},1)
 j=p["selected"][0]
 save_checkpoint(j,20)
 assert resume_command(j)["resume_from_frame"]==20
 retry_job(j,"RENDER_TIMEOUT",3)
 k=cache_key("c",{"x":1}); store({},k,{"verified":True})
 c={}; store(c,k,{"verified":True}); assert lookup(c,k)["verified"]
