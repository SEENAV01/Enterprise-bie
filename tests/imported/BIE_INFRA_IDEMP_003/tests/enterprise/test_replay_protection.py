
import unittest
from enterprise.replay_protection import *
class T(unittest.TestCase):
 def setUp(self): self.now=100.; self.p=ReplayProtector(lambda:self.now)
 def tok(self,**kw):
  x=dict(token_id="t",scope="commit",issued_at=90.,expires_at=110.);x.update(kw);return ReplayToken(**x)
 def test_valid(self): self.assertTrue(self.p.validate_and_consume(self.tok(),"commit"))
 def test_consumed(self): self.p.validate_and_consume(self.tok(),"commit");self.assertTrue(self.p.consumed("t"))
 def test_replay(self):
  self.p.validate_and_consume(self.tok(),"commit")
  with self.assertRaises(ReplayError): self.p.validate_and_consume(self.tok(),"commit")
 def test_scope(self):
  with self.assertRaises(ReplayError): self.p.validate_and_consume(self.tok(),"ack")
 def test_expired(self):
  with self.assertRaises(ReplayError): self.p.validate_and_consume(self.tok(expires_at=100.),"commit")
 def test_future(self):
  with self.assertRaises(ReplayError): self.p.validate_and_consume(self.tok(issued_at=101.),"commit")
 def test_invalid_id(self):
  with self.assertRaises(ReplayError): self.p.validate_and_consume(self.tok(token_id=""),"commit")
if __name__=="__main__": unittest.main()
