import unittest, tempfile, sqlite3
from pathlib import Path
from bie.infrastructure.persistence import *

class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.db=SQLitePersistence(Path(self.tmp.name)/"bie.db")
        self.db.create_run("r1",{"SOURCE":[],"REASONING":["SOURCE"]})
    def tearDown(self): self.tmp.cleanup()

    def test_run_roundtrip(self):
        x=self.db.load_run_state("r1")
        self.assertEqual(x["run_state"],"CREATED")
        self.assertEqual(x["stages"]["SOURCE"]["attempts"][0]["state"],"PENDING")

    def test_attempt_persist(self):
        a=PersistedAttempt("SOURCE",1,"SUCCEEDED",[],["src"],["ev"])
        self.db.save_attempt("r1",a)
        x=self.db.load_run_state("r1")
        self.assertEqual(x["stages"]["SOURCE"]["attempts"][0]["output_artifact_refs"],["src"])

    def test_retry_attempt_append(self):
        self.db.save_attempt("r1",PersistedAttempt("SOURCE",1,"FAILED",evidence_refs=["e"],diagnostics=["x"],remediation_owner="BI"))
        self.db.save_attempt("r1",PersistedAttempt("SOURCE",2,"READY"))
        x=self.db.load_run_state("r1")
        self.assertEqual([a["attempt"] for a in x["stages"]["SOURCE"]["attempts"]],[1,2])
        self.assertEqual(x["stages"]["SOURCE"]["attempts"][0]["state"],"FAILED")

    def test_event_order(self):
        self.db.append_event("r1",PersistedEvent(0,"SOURCE","PENDING","READY",1,"t1","ready",[]))
        self.db.append_event("r1",PersistedEvent(0,"SOURCE","READY","RUNNING",1,"t2","run",[]))
        x=self.db.load_run_state("r1")
        self.assertEqual([e["to_state"] for e in x["events"]],["READY","RUNNING"])

    def test_run_state_update(self):
        self.db.set_run_state("r1","ACTIVE")
        self.assertEqual(self.db.load_run_state("r1")["run_state"],"ACTIVE")

    def test_artifact_lineage_roundtrip(self):
        src=PersistedArtifactRecord("src","source","sha256","a"*64,1,"r1","SOURCE",False,{},[])
        child=PersistedArtifactRecord("child","reason","sha256","b"*64,2,"r1","REASONING",True,{"x":1},["src"])
        self.db.register_artifact(src); self.db.register_artifact(child)
        out=self.db.load_artifact("child")
        self.assertEqual(out.parent_artifact_ids,["src"])
        self.assertTrue(out.evidence)
        self.assertEqual(self.db.evidence_for_run("r1"),["child"])

    def test_missing_parent_rejected(self):
        r=PersistedArtifactRecord("x","reason","sha256","c"*64,1,"r1","REASONING",False,{},["missing"])
        with self.assertRaises(PersistenceError): self.db.register_artifact(r)

    def test_artifact_immutable_conflict(self):
        r=PersistedArtifactRecord("a","x","sha256","d"*64,1,"r1","SOURCE",False,{},[])
        self.db.register_artifact(r)
        bad=PersistedArtifactRecord("a","x","sha256","e"*64,1,"r1","SOURCE",False,{},[])
        with self.assertRaises(PersistenceError): self.db.register_artifact(bad)

    def test_idempotent_artifact_reregister(self):
        r=PersistedArtifactRecord("a","x","sha256","d"*64,1,"r1","SOURCE",False,{"k":"v"},[])
        self.db.register_artifact(r); self.db.register_artifact(r)
        self.assertEqual(self.db.artifacts_for_run("r1"),["a"])

    def test_schema_version_fail_closed(self):
        path=Path(self.tmp.name)/"bad.db"
        c=sqlite3.connect(path)
        c.execute("CREATE TABLE schema_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
        c.execute("INSERT INTO schema_meta VALUES('schema_version','999')")
        c.commit(); c.close()
        with self.assertRaises(PersistenceError): SQLitePersistence(path)

    def test_transactional_create_run(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.create_run("r1",{"X":[]})
        x=self.db.load_run_state("r1")
        self.assertNotIn("X",x["stages"])

if __name__=="__main__": unittest.main()
