import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from events import event
from metrics import render_metrics
from analytics import failure_summary
from audit import audit_record,verify_audit
def test_m264():
 e=[event("RENDER_STARTED","r"),event("RENDER_SUCCEEDED","r")]
 assert render_metrics(e)["success_rate"]==50.0
 f=[event("RENDER_FAILED","r",{"code":"X"},"ERROR")]
 assert failure_summary(f)[0]["code"]=="X"
 assert verify_audit([audit_record("r","system","RENDER","s","OK")])["valid"]
