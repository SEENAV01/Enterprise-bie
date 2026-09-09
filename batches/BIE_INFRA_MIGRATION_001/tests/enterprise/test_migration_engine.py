
import unittest,sqlite3
from enterprise.migration_engine import *
class T(unittest.TestCase):
 def db(self): return sqlite3.connect(":memory:")
 def test_empty(self): self.assertEqual(MigrationEngine(self.db(),[]).current(),0)
 def test_apply(self):
  e=MigrationEngine(self.db(),[Migration(1,"a","CREATE TABLE x(id INTEGER);")]);self.assertEqual(e.apply_to_latest(),1)
 def test_two(self):
  e=MigrationEngine(self.db(),[Migration(1,"a","CREATE TABLE x(id INTEGER);"),Migration(2,"b","ALTER TABLE x ADD COLUMN y TEXT;")]);self.assertEqual(e.apply_to_latest(),2)
 def test_idempotent(self):
  e=MigrationEngine(self.db(),[Migration(1,"a","CREATE TABLE x(id INTEGER);")]);e.apply_to_latest();self.assertEqual(e.apply_to_latest(),1)
 def test_gap(self):
  with self.assertRaises(MigrationError): MigrationEngine(self.db(),[Migration(2,"b","SELECT 1;")])
 def test_failure(self):
  e=MigrationEngine(self.db(),[Migration(1,"bad","INVALID SQL")])
  with self.assertRaises(MigrationError): e.apply_to_latest()
if __name__=="__main__": unittest.main()
