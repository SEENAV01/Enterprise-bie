"""Adjunct operator-control/audit store.

This store does not replace canonical run state. Control requests remain REQUESTED
until a trusted worker adapter explicitly acknowledges them.
"""
from __future__ import annotations
from pathlib import Path
import json, sqlite3, time

ACTIONS={"PAUSE","RESUME","CANCEL"}
class ControlStoreError(ValueError): pass

class OperatorControlStore:
    def __init__(self,path:Path,clock=None):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True);self.clock=clock or time.time;self._init()
    def _connect(self):
        c=sqlite3.connect(str(self.path),timeout=30,isolation_level=None);c.row_factory=sqlite3.Row;return c
    def _init(self):
        with self._connect() as c:
            c.executescript("""
            BEGIN IMMEDIATE;
            CREATE TABLE IF NOT EXISTS app_run_meta(run_id TEXT PRIMARY KEY,profile TEXT NOT NULL,config_hash TEXT NOT NULL,created_at REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS app_source_validation(run_id TEXT PRIMARY KEY,payload_json TEXT NOT NULL,recorded_at REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS app_control_requests(
              request_id INTEGER PRIMARY KEY AUTOINCREMENT,run_id TEXT NOT NULL,action TEXT NOT NULL,status TEXT NOT NULL,
              reason TEXT NOT NULL,requested_at REAL NOT NULL,acknowledged_at REAL,worker_ref TEXT);
            CREATE INDEX IF NOT EXISTS idx_app_control_run ON app_control_requests(run_id,request_id);
            COMMIT;
            """)
    def put_run_meta(self,run_id,profile,config_hash):
        with self._connect() as c:c.execute("INSERT INTO app_run_meta(run_id,profile,config_hash,created_at) VALUES(?,?,?,?)",(run_id,profile,config_hash,float(self.clock())))
    def run_meta(self,run_id):
        with self._connect() as c:
            r=c.execute("SELECT run_id,profile,config_hash,created_at FROM app_run_meta WHERE run_id=?",(run_id,)).fetchone();return dict(r) if r else None
    def put_source_validation(self,run_id,record):
        encoded=json.dumps(record,sort_keys=True,separators=(",",":"))
        with self._connect() as c:c.execute("""INSERT INTO app_source_validation(run_id,payload_json,recorded_at) VALUES(?,?,?)
        ON CONFLICT(run_id) DO UPDATE SET payload_json=excluded.payload_json,recorded_at=excluded.recorded_at""",(run_id,encoded,float(self.clock())))
    def source_validation(self,run_id):
        with self._connect() as c:
            r=c.execute("SELECT payload_json,recorded_at FROM app_source_validation WHERE run_id=?",(run_id,)).fetchone()
            if not r:return None
            v=json.loads(r["payload_json"]);v["recorded_at"]=r["recorded_at"];return v
    def request(self,run_id,action,reason):
        if action not in ACTIONS:raise ControlStoreError("unsupported control action")
        if type(reason) is not str or not reason.strip() or len(reason)>500:raise ControlStoreError("control reason required")
        with self._connect() as c:
            if c.execute("SELECT 1 FROM app_control_requests WHERE run_id=? AND status='REQUESTED' LIMIT 1",(run_id,)).fetchone():
                raise ControlStoreError("control request already pending")
            rid=int(c.execute("""INSERT INTO app_control_requests(run_id,action,status,reason,requested_at) VALUES(?,?,?,?,?)""",
                (run_id,action,"REQUESTED",reason.strip(),float(self.clock()))).lastrowid)
        return self.get(rid)
    def acknowledge(self,request_id,worker_ref):
        if type(worker_ref) is not str or not worker_ref.strip():raise ControlStoreError("worker ref required")
        with self._connect() as c:
            r=c.execute("SELECT status FROM app_control_requests WHERE request_id=?",(request_id,)).fetchone()
            if not r:raise ControlStoreError("control request not found")
            if r["status"]!="REQUESTED":raise ControlStoreError("control request not pending")
            c.execute("UPDATE app_control_requests SET status='EFFECTIVE',acknowledged_at=?,worker_ref=? WHERE request_id=?",
                      (float(self.clock()),worker_ref.strip(),request_id))
        return self.get(request_id)
    def get(self,request_id):
        with self._connect() as c:
            r=c.execute("""SELECT request_id,run_id,action,status,reason,requested_at,acknowledged_at,worker_ref
                           FROM app_control_requests WHERE request_id=?""",(request_id,)).fetchone()
            if not r:raise ControlStoreError("control request not found")
            return dict(r)
    def latest(self,run_id):
        with self._connect() as c:
            r=c.execute("""SELECT request_id,run_id,action,status,reason,requested_at,acknowledged_at,worker_ref
                           FROM app_control_requests WHERE run_id=? ORDER BY request_id DESC LIMIT 1""",(run_id,)).fetchone()
            return dict(r) if r else None
    def events(self,run_id):
        with self._connect() as c:
            rows=c.execute("""SELECT request_id,action,status,reason,requested_at,acknowledged_at,worker_ref
                              FROM app_control_requests WHERE run_id=? ORDER BY request_id""",(run_id,)).fetchall()
            return [dict(r) for r in rows]
