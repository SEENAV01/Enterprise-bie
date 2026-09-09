
import unittest
from enterprise.tracing import *
class T(unittest.TestCase):
 def test_root(self): self.assertIsNone(Tracer().start("x").parent_id)
 def test_child_trace(self):
  t=Tracer();a=t.start("a");b=t.start("b",parent_id=a.span_id);self.assertEqual(a.trace_id,b.trace_id)
 def test_unknown_parent(self):
  with self.assertRaises(TraceError): Tracer().start("x",parent_id="z")
 def test_finish(self): 
  t=Tracer();s=t.start("x");self.assertEqual(t.finish(s.span_id).status,"OK")
 def test_double_finish(self):
  t=Tracer();s=t.start("x");t.finish(s.span_id)
  with self.assertRaises(TraceError): t.finish(s.span_id)
if __name__=="__main__": unittest.main()
