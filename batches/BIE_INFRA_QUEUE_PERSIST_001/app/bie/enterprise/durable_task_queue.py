from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Callable
import sqlite3, json, time

class DurableQueueError(ValueError): pass

SCHEMA_VERSION=1
VALID_STATES={"READY","DELIVERED","ACKED","DEAD_LETTER"}

@dataclass(frozen=True)
class DurableTaskMessage:
    task_id:str
    run_id:str
    stage_id:str
    attempt:int
    idempotency_key:str
    required_capability_tags:List[str]
    input_artifact_refs:List[str]
    priority:int=100
    max_deliveries:int=5
    created_at:float=0.0

    def validate(self):
        if not self.task_id or not self.run_id or not self.stage_id or not self.idempotency_key:
            raise DurableQueueError("task identity fields required")
        if self.attempt<1: raise DurableQueueError("attempt must be >=1")
        if self.priority<0: raise DurableQueueError("priority must be >=0")
        if self.max_deliveries<1: raise DurableQueueError("max_deliveries must be >=1")

@dataclass(frozen=True)
class DurableDelivery:
    task:DurableTaskMessage
    delivery_count:int
    state:str
    consumer_id:Optional[str]
    visible_at:float
    delivered_at:Optional[float]
    acked_at:Optional[float]
    last_reason:str

class SQLiteDurableTaskQueue:
    def __init__(self,path:Path,clock:Optional[Callable[[],float]]=None,max_queued:int=10000,max_in_flight:int=1000):
        if max_queued<1 or max_in_flight<1:
            raise DurableQueueError("queue limits must be >=1")
        self.path=Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.clock=clock or time.time
        self.max_queued=max_queued
        self.max_in_flight=max_in_flight
        self._init_db()

    def _now(self): return float(self.clock())

    def _connect(self):
        c=sqlite3.connect(str(self.path),timeout=30,isolation_level=None)
        c.execute("PRAGMA foreign_keys=ON")
        c.execute("PRAGMA journal_mode=WAL")
        return c

    def _init_db(self):
        c=self._connect()
        try:
            c.executescript("""
            BEGIN IMMEDIATE;
            CREATE TABLE IF NOT EXISTS schema_meta(
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS queue_tasks(
                task_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                stage_id TEXT NOT NULL,
                attempt INTEGER NOT NULL,
                idempotency_key TEXT NOT NULL,
                capability_tags_json TEXT NOT NULL,
                input_refs_json TEXT NOT NULL,
                priority INTEGER NOT NULL,
                max_deliveries INTEGER NOT NULL,
                created_at REAL NOT NULL,
                delivery_count INTEGER NOT NULL DEFAULT 0,
                state TEXT NOT NULL,
                consumer_id TEXT,
                visible_at REAL NOT NULL,
                delivered_at REAL,
                acked_at REAL,
                last_reason TEXT NOT NULL DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_queue_ready
                ON queue_tasks(state,priority,created_at,task_id);
            CREATE INDEX IF NOT EXISTS idx_queue_visibility
                ON queue_tasks(state,visible_at);
            CREATE INDEX IF NOT EXISTS idx_queue_run
                ON queue_tasks(run_id,stage_id);
            CREATE TABLE IF NOT EXISTS queue_events(
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_at REAL NOT NULL,
                consumer_id TEXT,
                delivery_count INTEGER NOT NULL,
                reason TEXT NOT NULL,
                FOREIGN KEY(task_id) REFERENCES queue_tasks(task_id) ON DELETE CASCADE
            );
            COMMIT;
            """)
            row=c.execute("SELECT value FROM schema_meta WHERE key='schema_version'").fetchone()
            if row is None:
                c.execute("INSERT INTO schema_meta(key,value) VALUES('schema_version',?)",(str(SCHEMA_VERSION),))
            elif int(row[0])!=SCHEMA_VERSION:
                raise DurableQueueError(f"unsupported schema version {row[0]}")
        finally:
            c.close()

    def _event(self,c,task_id,event_type,consumer_id,delivery_count,reason):
        c.execute("""INSERT INTO queue_events(task_id,event_type,event_at,consumer_id,delivery_count,reason)
                     VALUES(?,?,?,?,?,?)""",
                  (task_id,event_type,self._now(),consumer_id,delivery_count,reason))

    def _semantic_tuple(self,msg:DurableTaskMessage):
        return (
            msg.run_id,msg.stage_id,msg.attempt,msg.idempotency_key,
            json.dumps(list(msg.required_capability_tags),sort_keys=True),
            json.dumps(list(msg.input_artifact_refs),sort_keys=True),
            msg.priority,msg.max_deliveries
        )

    def enqueue(self,msg:DurableTaskMessage)->None:
        msg.validate()
        c=self._connect()
        try:
            c.execute("BEGIN IMMEDIATE")
            row=c.execute("""SELECT run_id,stage_id,attempt,idempotency_key,capability_tags_json,input_refs_json,
                                    priority,max_deliveries FROM queue_tasks WHERE task_id=?""",(msg.task_id,)).fetchone()
            if row is not None:
                existing=(
                    row[0],row[1],row[2],row[3],
                    json.dumps(json.loads(row[4]),sort_keys=True),
                    json.dumps(json.loads(row[5]),sort_keys=True),
                    row[6],row[7]
                )
                if existing!=self._semantic_tuple(msg):
                    raise DurableQueueError("task_id conflict")
                c.execute("COMMIT")
                return

            ready=c.execute("SELECT COUNT(*) FROM queue_tasks WHERE state='READY'").fetchone()[0]
            if ready>=self.max_queued:
                raise DurableQueueError("queue backpressure: max queued reached")

            created=msg.created_at or self._now()
            c.execute("""INSERT INTO queue_tasks(
                task_id,run_id,stage_id,attempt,idempotency_key,capability_tags_json,input_refs_json,
                priority,max_deliveries,created_at,delivery_count,state,consumer_id,visible_at,
                delivered_at,acked_at,last_reason)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (msg.task_id,msg.run_id,msg.stage_id,msg.attempt,msg.idempotency_key,
                 json.dumps(list(msg.required_capability_tags),sort_keys=True),
                 json.dumps(list(msg.input_artifact_refs),sort_keys=True),
                 msg.priority,msg.max_deliveries,created,0,"READY",None,self._now(),None,None,""))
            self._event(c,msg.task_id,"ENQUEUED",None,0,"enqueued")
            c.execute("COMMIT")
        except Exception:
            c.execute("ROLLBACK")
            raise
        finally:
            c.close()

    def recover_expired(self)->int:
        c=self._connect()
        recovered=0
        try:
            c.execute("BEGIN IMMEDIATE")
            rows=c.execute("""SELECT task_id,delivery_count,max_deliveries,consumer_id
                              FROM queue_tasks WHERE state='DELIVERED' AND visible_at<=?
                              ORDER BY task_id""",(self._now(),)).fetchall()
            for task_id,count,maxd,consumer in rows:
                if count>=maxd:
                    c.execute("""UPDATE queue_tasks SET state='DEAD_LETTER',consumer_id=NULL,last_reason=?
                                 WHERE task_id=?""",("visibility timeout: max deliveries exceeded",task_id))
                    self._event(c,task_id,"DEAD_LETTERED",consumer,count,"visibility timeout: max deliveries exceeded")
                else:
                    c.execute("""UPDATE queue_tasks SET state='READY',consumer_id=NULL,visible_at=?,last_reason=?
                                 WHERE task_id=?""",(self._now(),"visibility timeout",task_id))
                    self._event(c,task_id,"VISIBILITY_RECOVERED",consumer,count,"visibility timeout")
                recovered+=1
            c.execute("COMMIT")
            return recovered
        except Exception:
            c.execute("ROLLBACK"); raise
        finally:
            c.close()

    def poll(self,consumer_id:str,visibility_timeout:float=30.0,capability_tags:Optional[List[str]]=None)->Optional[DurableDelivery]:
        if not consumer_id: raise DurableQueueError("consumer_id required")
        if visibility_timeout<=0: raise DurableQueueError("visibility_timeout must be >0")
        self.recover_expired()
        caps=set(capability_tags or [])
        c=self._connect()
        try:
            c.execute("BEGIN IMMEDIATE")
            inflight=c.execute("SELECT COUNT(*) FROM queue_tasks WHERE state='DELIVERED'").fetchone()[0]
            if inflight>=self.max_in_flight:
                c.execute("COMMIT"); return None

            rows=c.execute("""SELECT task_id,capability_tags_json FROM queue_tasks
                              WHERE state='READY' AND visible_at<=?
                              ORDER BY priority ASC,created_at ASC,task_id ASC""",(self._now(),)).fetchall()
            chosen=None
            for task_id,tags_json in rows:
                req=set(json.loads(tags_json))
                if req.issubset(caps):
                    chosen=task_id; break
            if chosen is None:
                c.execute("COMMIT"); return None

            row=c.execute("SELECT delivery_count FROM queue_tasks WHERE task_id=?",(chosen,)).fetchone()
            count=row[0]+1
            delivered=self._now()
            visible=delivered+visibility_timeout
            c.execute("""UPDATE queue_tasks
                         SET delivery_count=?,state='DELIVERED',consumer_id=?,delivered_at=?,visible_at=?,last_reason=?
                         WHERE task_id=? AND state='READY'""",
                      (count,consumer_id,delivered,visible,"delivered",chosen))
            if c.total_changes==0:
                raise DurableQueueError("delivery race")
            self._event(c,chosen,"DELIVERED",consumer_id,count,"delivered")
            c.execute("COMMIT")
            return self.get(chosen)
        except Exception:
            c.execute("ROLLBACK"); raise
        finally:
            c.close()

    def ack(self,task_id:str,consumer_id:str)->None:
        c=self._connect()
        try:
            c.execute("BEGIN IMMEDIATE")
            row=c.execute("SELECT state,consumer_id,delivery_count FROM queue_tasks WHERE task_id=?",(task_id,)).fetchone()
            if row is None: raise DurableQueueError("task not found")
            if row[0]!="DELIVERED": raise DurableQueueError("task not delivered")
            if row[1]!=consumer_id: raise DurableQueueError("consumer ownership mismatch")
            c.execute("""UPDATE queue_tasks SET state='ACKED',acked_at=?,last_reason=? WHERE task_id=?""",
                      (self._now(),"acked",task_id))
            self._event(c,task_id,"ACKED",consumer_id,row[2],"acked")
            c.execute("COMMIT")
        except Exception:
            c.execute("ROLLBACK"); raise
        finally:
            c.close()

    def nack(self,task_id:str,consumer_id:str,delay_seconds:float=0.0,reason:str="nack")->None:
        if delay_seconds<0: raise DurableQueueError("delay must be >=0")
        c=self._connect()
        try:
            c.execute("BEGIN IMMEDIATE")
            row=c.execute("""SELECT state,consumer_id,delivery_count,max_deliveries
                             FROM queue_tasks WHERE task_id=?""",(task_id,)).fetchone()
            if row is None: raise DurableQueueError("task not found")
            if row[0]!="DELIVERED": raise DurableQueueError("task not delivered")
            if row[1]!=consumer_id: raise DurableQueueError("consumer ownership mismatch")
            if row[2]>=row[3]:
                state="DEAD_LETTER"; vis=self._now(); event="DEAD_LETTERED"
                last=f"{reason}: max deliveries exceeded"
            else:
                state="READY"; vis=self._now()+delay_seconds; event="NACKED"
                last=reason
            c.execute("""UPDATE queue_tasks SET state=?,consumer_id=NULL,visible_at=?,last_reason=?
                         WHERE task_id=?""",(state,vis,last,task_id))
            self._event(c,task_id,event,consumer_id,row[2],last)
            c.execute("COMMIT")
        except Exception:
            c.execute("ROLLBACK"); raise
        finally:
            c.close()

    def dead_letter(self,task_id:str,reason:str)->None:
        c=self._connect()
        try:
            c.execute("BEGIN IMMEDIATE")
            row=c.execute("SELECT state,consumer_id,delivery_count FROM queue_tasks WHERE task_id=?",(task_id,)).fetchone()
            if row is None: raise DurableQueueError("task not found")
            if row[0]=="ACKED": raise DurableQueueError("cannot dead-letter acked task")
            c.execute("UPDATE queue_tasks SET state='DEAD_LETTER',consumer_id=NULL,last_reason=? WHERE task_id=?",
                      (reason,task_id))
            self._event(c,task_id,"DEAD_LETTERED",row[1],row[2],reason)
            c.execute("COMMIT")
        except Exception:
            c.execute("ROLLBACK"); raise
        finally:
            c.close()

    def redrive(self,task_id:str)->None:
        c=self._connect()
        try:
            c.execute("BEGIN IMMEDIATE")
            row=c.execute("SELECT state,delivery_count FROM queue_tasks WHERE task_id=?",(task_id,)).fetchone()
            if row is None: raise DurableQueueError("task not found")
            if row[0]!="DEAD_LETTER": raise DurableQueueError("only dead-letter task can redrive")
            c.execute("""UPDATE queue_tasks SET state='READY',consumer_id=NULL,visible_at=?,last_reason=?
                         WHERE task_id=?""",(self._now(),"manual redrive",task_id))
            self._event(c,task_id,"REDRIVEN",None,row[1],"manual redrive")
            c.execute("COMMIT")
        except Exception:
            c.execute("ROLLBACK"); raise
        finally:
            c.close()

    def get(self,task_id:str)->DurableDelivery:
        c=self._connect()
        try:
            r=c.execute("""SELECT task_id,run_id,stage_id,attempt,idempotency_key,capability_tags_json,input_refs_json,
                           priority,max_deliveries,created_at,delivery_count,state,consumer_id,visible_at,
                           delivered_at,acked_at,last_reason
                           FROM queue_tasks WHERE task_id=?""",(task_id,)).fetchone()
            if r is None: raise DurableQueueError("task not found")
            msg=DurableTaskMessage(r[0],r[1],r[2],r[3],r[4],json.loads(r[5]),json.loads(r[6]),r[7],r[8],r[9])
            return DurableDelivery(msg,r[10],r[11],r[12],r[13],r[14],r[15],r[16])
        finally:
            c.close()

    def stats(self)->Dict[str,int]:
        self.recover_expired()
        c=self._connect()
        try:
            out={s:0 for s in VALID_STATES}
            for state,count in c.execute("SELECT state,COUNT(*) FROM queue_tasks GROUP BY state").fetchall():
                out[state]=count
            return out
        finally:
            c.close()

    def events(self,task_id:str)->List[Dict[str,object]]:
        c=self._connect()
        try:
            rows=c.execute("""SELECT sequence,event_type,event_at,consumer_id,delivery_count,reason
                              FROM queue_events WHERE task_id=? ORDER BY sequence""",(task_id,)).fetchall()
            return [{"sequence":r[0],"event_type":r[1],"event_at":r[2],"consumer_id":r[3],
                     "delivery_count":r[4],"reason":r[5]} for r in rows]
        finally:
            c.close()
