import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_fault_tolerance

def test_duplicate_blocked():
 r=compile_fault_tolerance({}, {}, "2026-01-01",
   error=None, completed_keys=["abc"], key="abc")
 assert not r["quality_gate"]["valid"]

def test_retry_allowed():
 r=compile_fault_tolerance({}, {}, "2026-01-01",
   error="TIMEOUT", attempt=1,
   retry={"max_attempts":3,"backoff_seconds":10,
          "retryable_errors":["TIMEOUT"]})
 assert r["retry"]["allowed"]
