
class PostgresAdapterError(ValueError):pass
class PostgresAdapter:
 def __init__(self,connection_factory):self.factory=connection_factory
 def transaction(self,fn):
  c=self.factory()
  try:
   out=fn(c);c.commit();return out
  except Exception:
   c.rollback();raise
  finally:c.close()
 def health(self):
  def q(c):
   cur=c.cursor();cur.execute("SELECT 1");return cur.fetchone()[0]==1
  return self.transaction(q)
