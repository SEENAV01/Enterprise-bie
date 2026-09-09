
import unittest
from book_intelligence.ocr_reconciliation import *
class T(unittest.TestCase):
 def c(self,t,c,s):return Candidate(t,c,s)
 def test_agree(self):self.assertEqual(reconcile(self.c("x",.8,"n"),self.c("x",.9,"o"))[1],"AGREE")
 def test_win(self):self.assertEqual(reconcile(self.c("a",.5,"n"),self.c("b",.9,"o"))[0].text,"b")
 def test_review(self):self.assertEqual(reconcile(self.c("a",.8,"n"),self.c("b",.85,"o"))[1],"CONFLICT_REVIEW")
 def test_single(self):self.assertEqual(reconcile(None,self.c("b",.9,"o"))[1],"SINGLE_SOURCE")
 def test_none(self):
  with self.assertRaises(ReconcileError):reconcile(None,None)
if __name__=="__main__":unittest.main()
