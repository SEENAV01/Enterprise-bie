import unittest
from bie.game_engine.build_runtime_engine.exception_capture import capture_node_exception,capture_browser_exception
from tests.build_runtime_engine.support import built
class ExceptionSecurity(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.td,cls.ctx,cls.assets,cls.ws=built()
 @classmethod
 def tearDownClass(cls):cls.td.cleanup()
 def test_node_raw_stack_not_persisted(self):self.assertFalse(capture_node_exception().raw_stack_persisted)
 def test_browser_raw_stack_not_persisted(self):self.assertFalse(capture_browser_exception(self.ws.root/'dist').raw_stack_persisted)
 def test_node_hash_is_digest(self):self.assertEqual(len(capture_node_exception().stack_sha256),64)
 def test_browser_hash_is_digest(self):self.assertEqual(len(capture_browser_exception(self.ws.root/'dist').stack_sha256),64)
 def test_exception_codes_are_stable(self):self.assertEqual(capture_node_exception().message_code,'BIE_RUNTIME_FIXTURE');self.assertEqual(capture_browser_exception(self.ws.root/'dist').message_code,'BIE_BROWSER_FIXTURE')
