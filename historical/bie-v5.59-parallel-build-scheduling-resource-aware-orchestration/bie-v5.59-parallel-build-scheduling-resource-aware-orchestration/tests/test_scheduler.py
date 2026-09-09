import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from scheduler import schedule

def test_parallel_ready_jobs():
 jobs=[
  {"job_id":"a","dependencies":[],"resources":{"cpu":2}},
  {"job_id":"b","dependencies":[],"resources":{"cpu":2}},
  {"job_id":"c","dependencies":["a","b"],"resources":{"cpu":1}}]
 r=schedule(jobs,[],{"cpu":4})
 assert r["scheduled"]==["a","b"]

def test_dependency_wait():
 jobs=[
  {"job_id":"a","dependencies":[],"resources":{"cpu":1}},
  {"job_id":"b","dependencies":["a"],"resources":{"cpu":1}}]
 r=schedule(jobs,[],{"cpu":2})
 assert r["scheduled"]==["a"]
