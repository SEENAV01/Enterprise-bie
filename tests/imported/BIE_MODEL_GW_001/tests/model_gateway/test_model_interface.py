
import unittest
from bie.model_gateway.model_interface import *
class T(unittest.TestCase):
 def test_valid(self):self.assertTrue(validate_request(ModelRequest("r",({"role":"user","content":"x"},))))
 def test_id(self):
  with self.assertRaises(GatewayError):validate_request(ModelRequest("",("x",)))
 def test_messages(self):
  with self.assertRaises(GatewayError):validate_request(ModelRequest("r",()))
 def test_temp(self):
  with self.assertRaises(GatewayError):validate_request(ModelRequest("r",("x",),temperature=3))
 def test_response(self):self.assertEqual(ModelResponse("p","m","x",{},"stop",{}).provider,"p")
if __name__=="__main__":unittest.main()
