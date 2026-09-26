import unittest
from bie.game_engine.build_runtime_engine.exception_capture import capture_node_exception,capture_browser_exception
from tests.build_runtime_engine.support import built
class Build005(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.td,cls.ctx,cls.assets,cls.ws=built()
 @classmethod
 def tearDownClass(cls):cls.td.cleanup()
 def test_node_exception_captured(self):self.assertEqual(capture_node_exception().message_code,'BIE_RUNTIME_FIXTURE')
 def test_browser_exception_captured(self):self.assertEqual(capture_browser_exception(self.ws.root/'dist').message_code,'BIE_BROWSER_FIXTURE')
 def test_node_stack_only_hashed(self):self.assertFalse(capture_node_exception().raw_stack_persisted)
 def test_browser_stack_only_hashed(self):self.assertFalse(capture_browser_exception(self.ws.root/'dist').raw_stack_persisted)
 def test_exception_hashes_stable_shape(self):self.assertEqual(len(capture_node_exception().stack_sha256),64)
 def test_no_product_acceptance(self):self.assertFalse(capture_browser_exception(self.ws.root/'dist').product_accepted)
