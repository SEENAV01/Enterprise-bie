
from dataclasses import dataclass
class MigrationError(RuntimeError): pass
@dataclass(frozen=True)
class Migration:
 version:int; name:str; up_sql:str; down_sql:str|None=None
class MigrationEngine:
 def __init__(self,db,migrations):
  self.db=db; self.migrations=sorted(migrations,key=lambda m:m.version)
  vs=[m.version for m in self.migrations]
  if vs and vs!=list(range(1,max(vs)+1)): raise MigrationError("migration versions must be contiguous from 1")
  self.db.execute("CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY,name TEXT NOT NULL)")
  self.db.commit()
 def current(self):
  r=self.db.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0]; return r or 0
 def apply_to_latest(self):
  for m in self.migrations:
   if m.version>self.current():
    try:
     with self.db:
      self.db.executescript(m.up_sql)
      self.db.execute("INSERT INTO schema_migrations VALUES(?,?)",(m.version,m.name))
    except Exception as e: raise MigrationError(f"migration {m.version} failed: {e}")
  return self.current()
