import unittest
from bie.document_intelligence.real_pdf_contract import *
class T(unittest.TestCase):
 def test_contract(self):
  d=b"%PDF-1.7 sample";self.assertEqual(inspect_pdf(d,2)["page_count"],2)
  self.assertEqual(len(inspect_pdf(d,1)["source_hash"]),64)
  with self.assertRaises(E):inspect_pdf(b"bad",1)
  with self.assertRaises(E):inspect_pdf(d,0)
if __name__=='__main__':unittest.main()
