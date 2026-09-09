
import tempfile
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parents[1]))
from bie_core.orchestrator import Pipeline,StateStore
from bie_core.mock_pipeline import register_demo_handlers

def test_full_pipeline():
    with tempfile.TemporaryDirectory() as d:
        p=Pipeline(StateStore(d)); register_demo_handlers(p)
        job,out=p.run("book.pdf",initial={"source_path":"book.pdf"})
        assert len(out)==8
        assert all(str(r.status)=="Status.PASS" for r in job.stages.values())
        assert job.stages["M8"].attempts==1

def test_state_persists():
    with tempfile.TemporaryDirectory() as d:
        p=Pipeline(StateStore(d)); register_demo_handlers(p)
        job,_=p.run("book.pdf",initial={"source_path":"book.pdf"},job_id="abc")
        saved=p.store.load("abc")
        assert saved["job_id"]=="abc"
        assert saved["stages"]["M5"]["status"]=="PASS"
