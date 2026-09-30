import unittest
from h5_support import assert_error
from bie.evaluation.benchmarks.browser.served.origin import *
class H5002(unittest.TestCase):
 def test_module_mime(self):self.assertEqual(headers('app.mjs',b'x')['Content-Type'],'text/javascript')
 def test_json_mime(self):self.assertEqual(headers('lesson.json',b'{}')['Content-Type'],'application/json')
 def test_no_eval_or_inline_grant(self):self.assertNotIn('unsafe-',CSP)
 def test_nosniff(self):self.assertEqual(HEADERS['X-Content-Type-Options'],'nosniff')
 def test_no_cache(self):self.assertEqual(HEADERS['Cache-Control'],'no-store')
 def test_exact_origin(self):self.assertEqual(route_path('http://127.0.0.1:5000/a.mjs','http://127.0.0.1:5000','GET',{'a.mjs'}),'a.mjs')
 def test_other_port_denied(self):assert_error(self,lambda:route_path('http://127.0.0.1:5001/a.js','http://127.0.0.1:5000','GET',{'a.js'}),'HTTP_ROUTE_DENIED')
 def test_credentials_denied(self):assert_error(self,lambda:route_path('http://a@127.0.0.1:5000/a.js','http://127.0.0.1:5000','GET',{'a.js'}))
 def test_post_denied(self):assert_error(self,lambda:route_path('http://127.0.0.1:5000/a.js','http://127.0.0.1:5000','POST',{'a.js'}))
 def test_traversal_denied(self):assert_error(self,lambda:request_path('/../a.js'),'HTTP_PATH_REJECTED')
 def test_encoded_traversal_denied(self):assert_error(self,lambda:request_path('/%2e%2e/a.js'),'HTTP_PATH_REJECTED')
 def test_query_rejected(self):assert_error(self,lambda:request_path('/a.js?x=1'),'HTTP_PATH_REJECTED')
 def test_backslash_denied(self):assert_error(self,lambda:request_path('/a\\b.js'),'HTTP_PATH_REJECTED')
 def test_unlisted_file_denied(self):assert_error(self,lambda:route_path('http://127.0.0.1:5000/b.js','http://127.0.0.1:5000','GET',{'a.js'}))
