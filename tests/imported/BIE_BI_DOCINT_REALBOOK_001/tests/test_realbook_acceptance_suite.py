import unittest
from bie.document_intelligence.realbook_acceptance_suite import *
class T(unittest.TestCase):
 def test_contract(self):
  books=[{"id":d,"domain":d,"source_hash":"a"*64,"gates":{g:True for g in GATES}} for d in REQUIRED]
  self.assertTrue(evaluate(books)["passed"])
  self.assertEqual(evaluate(books)["books"],5)
  with self.assertRaises(E):evaluate(books[:-1])
  bad=[dict(x) for x in books];bad[0]={**bad[0],"gates":{**bad[0]["gates"],"source_loss":False}}
  self.assertFalse(evaluate(bad)["passed"])
if __name__=='__main__':unittest.main()
