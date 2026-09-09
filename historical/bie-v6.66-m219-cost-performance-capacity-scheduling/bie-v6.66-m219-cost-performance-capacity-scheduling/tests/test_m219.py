import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from cost_model import job_cost
from capacity import capacity_forecast,required_workers
from binpack import pack
from admission import admit
def test_m219():
 j={"cpu_seconds":10,"gpu_seconds":2,"memory_gb_seconds":20}
 assert job_cost(j)>0
 assert capacity_forecast(3,1,4)["capacity"]==4
 assert required_workers(3,1,.75)==4
 assert len(pack([{"cpu":1,"memory":1,"gpu":0}],{"cpu":2,"memory":2,"gpu":0})["selected"])==1
 assert admit({"cpu":1,"memory":1,"gpu":0},{"cpu":2,"memory":2,"gpu":0},{"remaining_cost":10})["admitted"]
