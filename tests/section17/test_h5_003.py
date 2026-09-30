import unittest,http.client,hashlib,socket
from bie.evaluation.benchmarks.browser.served.server import serve
class H5003(unittest.TestCase):
 def request(self,s,path='/a.mjs',method='GET',headers=None):
  c=http.client.HTTPConnection('127.0.0.1',s.server_port,timeout=2)
  try:c.request(method,path,headers=headers or {});r=c.getresponse();return r.status,dict(r.getheaders()),r.read()
  finally:c.close()
 def test_actual_http_bytes(self):
  with serve({'a.mjs':b'export const x=3;'}) as s:
   status,h,raw=self.request(s);self.assertEqual(status,200);self.assertEqual(raw,b'export const x=3;')
 def test_actual_http_mime_and_csp(self):
  with serve({'a.mjs':b'x'}) as s:
   _,h,_=self.request(s);self.assertEqual(h['Content-Type'],'text/javascript');self.assertIn("script-src 'self'",h['Content-Security-Policy'])
 def test_head_has_no_body(self):
  with serve({'a.mjs':b'abc'}) as s:
   status,h,body=self.request(s,method='HEAD');self.assertEqual((status,h['Content-Length'],body),(200,'3',b''))
 def test_unknown_404(self):
  with serve({'a.mjs':b'x'}) as s:self.assertEqual(self.request(s,'/b.mjs')[0],404)
 def test_directory_not_listed(self):
  with serve({'a.mjs':b'x'}) as s:self.assertEqual(self.request(s,'/')[0],400)
 def test_bad_host_rejected(self):
  with serve({'a.mjs':b'x'}) as s:self.assertEqual(self.request(s,headers={'Host':'attacker.invalid'})[0],400)
 def test_post_rejected(self):
  with serve({'a.mjs':b'x'}) as s:self.assertEqual(self.request(s,method='POST')[0],405)
 def test_encoded_escape_rejected(self):
  with serve({'a.mjs':b'x'}) as s:self.assertEqual(self.request(s,'/%2e%2e/a.mjs')[0],400)
 def test_content_body_rejected(self):
  with serve({'a.mjs':b'x'}) as s:self.assertEqual(self.request(s,headers={'Content-Length':'1'})[0],400)
 def test_request_limit(self):
  with serve({'a.mjs':b'x'},max_requests=1) as s:
   self.assertEqual(self.request(s)[0],200);self.assertEqual(self.request(s)[0],429);self.assertTrue(s.snapshot()['limit_exceeded'])
 def test_response_byte_limit(self):
  with serve({'a.mjs':b'abc'},max_response_bytes=2) as s:self.assertEqual(self.request(s)[0],429)
 def test_transcript_hash_matches_bytes(self):
  with serve({'a.mjs':b'abc'}) as s:
   self.request(s);row=s.snapshot()['records'][0];self.assertEqual(row['sha256'],hashlib.sha256(b'abc').hexdigest());self.assertTrue(row['response_completed'])
 def test_port_closed_on_exit(self):
  with serve({'a.mjs':b'x'}) as s:port=s.server_port
  with socket.socket() as sock:self.assertNotEqual(sock.connect_ex(('127.0.0.1',port)),0)
 def test_no_origin_headers_from_candidate(self):
  with serve({'a.mjs':b'x'}) as s:self.assertNotIn('Access-Control-Allow-Origin',self.request(s)[1])

 def test_snapshot_waits_for_delayed_log_commit(self):
  import threading
  from unittest.mock import patch
  with serve({'a.mjs':b'abc'}) as s:
   entered=threading.Event();release=threading.Event();completed=threading.Event();result=[];original=s.log
   def delayed(row):
    entered.set();release.wait(1);original(row)
   def snapshot():
    try:result.append(s.snapshot())
    finally:completed.set()
   with patch.object(s,'log',delayed):
    self.request(s);self.assertTrue(entered.wait(1));worker=threading.Thread(target=snapshot);worker.start()
    try:self.assertFalse(completed.wait(.02))
    finally:release.set();worker.join(2)
    self.assertTrue(completed.is_set());self.assertEqual(len(result[0]['records']),1)
 def test_snapshot_timeout_is_fail_closed(self):
  from bie.evaluation.benchmarks.models import BenchmarkError
  with serve({'a.mjs':b'abc'}) as s:
   with s.condition:s.active_connections+=1
   try:
    with self.assertRaises(BenchmarkError) as cm:s.snapshot(quiesce_timeout=.01)
    self.assertEqual(cm.exception.code,'HTTP_SERVER_DRAIN_TIMEOUT')
   finally:
    with s.condition:s.active_connections-=1;s.condition.notify_all()
