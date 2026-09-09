
import unittest
from enterprise.postgres_adapter import *
class Cur:
 def execute(self,x):self.x=x
 def fetchone(self):return (1,)
class C:
 def __init__(self):self.com=False;self.rb=False;self.closed=False
 def cursor(self):return Cur()
 def commit(self):self.com=True
 def rollback(self):self.rb=True
 def close(self):self.closed=True
class T(unittest.TestCase):
 def test_health(self):self.assertTrue(PostgresAdapter(lambda:C()).health())
 def test_commit(self):
  c=C();PostgresAdapter(lambda:c).transaction(lambda x:3);self.assertTrue(c.com)
 def test_rollback(self):
  c=C()
  with self.assertRaises(RuntimeError):PostgresAdapter(lambda:c).transaction(lambda x:(_ for _ in ()).throw(RuntimeError()))
  self.assertTrue(c.rb)
 def test_close(self):
  c=C();PostgresAdapter(lambda:c).transaction(lambda x:1);self.assertTrue(c.closed)
if __name__=="__main__":unittest.main()
