
import unittest
from bie.document_intelligence.encryption_detection import *
class T(unittest.TestCase):
 def test_plain(self):self.assertEqual(gate(EncryptionStatus(False,True,True)),"EXTRACT")
 def test_extract(self):self.assertEqual(gate(EncryptionStatus(True,True,True,"std")),"EXTRACT")
 def test_render(self):self.assertEqual(gate(EncryptionStatus(True,False,True,"std")),"RENDER_ONLY")
 def test_block(self):
  with self.assertRaises(EncryptionError):gate(EncryptionStatus(True,False,False,"std"))
if __name__=="__main__":unittest.main()
