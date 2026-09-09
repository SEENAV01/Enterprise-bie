import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from dag import validate_dag,topological_order
from jobs import job,runnable
from retry import retry_decision

def test_dag():
 js=[job("a"),job("b",depends_on=["a"])]
 assert validate_dag(js)["valid"]
 assert topological_order(js)==["a","b"]

def test_runnable():
 j=job("b",depends_on=["a"])
 assert runnable(j,{"a"})

def test_retry():
 j=job("x",max_attempts=3); j["attempts"]=1
 assert retry_decision(j,"TIMEOUT")["retry"]
