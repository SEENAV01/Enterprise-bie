
from dataclasses import dataclass
import sqlite3,time
class IdempotencyError(RuntimeError): pass
@dataclass(frozen=True)
class Claim:
 key:str; fingerprint:str; state:str; owner:str; result_ref:str|None
class SQLiteIdempotencyStore:
 def __init__(self,path):
  self.db=sqlite3.connect(path); self.db.execute("PRAGMA journal_mode=WAL")
  self.db.execute("""CREATE TABLE IF NOT EXISTS claims(
   key TEXT PRIMARY KEY,fingerprint TEXT NOT NULL,state TEXT NOT NULL,
   owner TEXT NOT NULL,result_ref TEXT,created REAL NOT NULL,updated REAL NOT NULL)"""); self.db.commit()
 def claim(self,key,fingerprint,owner):
  if not key or not fingerprint or not owner: raise IdempotencyError("key/fingerprint/owner required")
  now=time.time()
  try:
   with self.db: self.db.execute("INSERT INTO claims VALUES(?,?,?,?,?,?,?)",(key,fingerprint,"CLAIMED",owner,None,now,now))
   return Claim(key,fingerprint,"CLAIMED",owner,None)
  except sqlite3.IntegrityError:
   r=self.get(key)
   if r.fingerprint!=fingerprint: raise IdempotencyError("idempotency key fingerprint conflict")
   return r
 def complete(self,key,owner,result_ref):
  r=self.get(key)
  if r.state=="COMPLETED":
   if r.result_ref!=result_ref: raise IdempotencyError("completed result conflict")
   return r
  if r.owner!=owner: raise IdempotencyError("foreign owner")
  if not result_ref: raise IdempotencyError("result ref required")
  with self.db: self.db.execute("UPDATE claims SET state='COMPLETED',result_ref=?,updated=? WHERE key=?",(result_ref,time.time(),key))
  return self.get(key)
 def get(self,key):
  row=self.db.execute("SELECT key,fingerprint,state,owner,result_ref FROM claims WHERE key=?",(key,)).fetchone()
  if not row: raise IdempotencyError("unknown claim")
  return Claim(*row)
 def close(self): self.db.close()
