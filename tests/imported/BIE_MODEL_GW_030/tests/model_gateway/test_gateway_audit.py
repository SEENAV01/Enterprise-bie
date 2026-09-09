
import unittest
from model_gateway.gateway_audit import *
class T(unittest.TestCase):
 def test_append(self):self.assertEqual(GatewayAudit().append("r","route",1).seq,1)
 def test_chain(self):
  a=GatewayAudit();x=a.append("r","route",1);y=a.append("r","invoke",2);self.assertEqual(y.prev_hash,x.event_hash)
 def test_verify(self):
  a=GatewayAudit();a.append("r","route",1);a.append("r","invoke",2,"p","m","d");self.assertTrue(a.verify())
 def test_required(self):
  with self.assertRaises(AuditError):GatewayAudit().append("","x",1)
 def test_provider(self):self.assertEqual(GatewayAudit().append("r","invoke",1,"p","m").provider,"p")
if __name__=="__main__":unittest.main()
