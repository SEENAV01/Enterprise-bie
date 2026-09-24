import unittest,time,threading,json
from unittest.mock import patch
from threading import Event
from bie.audio.neural_transport import _exchange,_bounded,_valid_call,OfficialNeuralTransport
from bie.audio.tts_contract import ProviderFailure
from tests.audio.neural_test_support import sleeper,die,huge_packet

class Response:
    status=200
    def __init__(self,body=b'{}',headers=None):self.body=body;self.pos=0;self.headers={'Content-Type':'application/json','Content-Length':str(len(body)),'request-id':'r1',**(headers or {})}
    def getheader(self,k,default=None):return self.headers.get(k,default)
    def read(self,n):b=self.body[self.pos:self.pos+n];self.pos+=len(b);return b
class Connection:
    def __init__(self,response):self.response=response;self.closed=False;self.sent=None
    def request(self,*a,**kw):self.sent=(a,kw)
    def getresponse(self):return self.response
    def close(self):self.closed=True
class TransportTests(unittest.TestCase):
    def call(self,r):
        self.conn=Connection(r)
        with patch('bie.audio.neural_transport.http.client.HTTPSConnection',return_value=self.conn) as factory:
            result=_exchange('GET','/v1/models',b'','fake_test_key',10000,1)
            self.assertEqual(factory.call_args.args,('api.elevenlabs.io',443));self.assertEqual(self.conn.sent[1]['headers']['xi-api-key'],'fake_test_key')
            return result
    def test_official_host_tls_and_response(self):self.assertEqual(self.call(Response()).body,b'{}');self.assertTrue(self.conn.closed)
    def test_redirect_does_not_follow(self):
        r=Response(headers={'Location':'https://evil.example'});r.status=302
        with self.assertRaisesRegex(ProviderFailure,'REDIRECT'):self.call(r)
        self.assertTrue(self.conn.closed)
    def test_content_type_rejected(self):
        with self.assertRaisesRegex(ProviderFailure,'CONTENT_TYPE'):self.call(Response(headers={'Content-Type':'text/html'}))
    def test_gzip_bomb_not_decoded(self):
        with self.assertRaisesRegex(ProviderFailure,'COMPRESSED'):self.call(Response(headers={'Content-Encoding':'gzip'}))
    def test_declared_size_bound(self):
        with self.assertRaisesRegex(ProviderFailure,'BUDGET'):self.call(Response(headers={'Content-Length':'10001'}))
    def test_streamed_size_bound(self):
        r=Response(b'x'*10001);r.headers.pop('Content-Length')
        with self.assertRaisesRegex(ProviderFailure,'BUDGET'):self.call(r)
    def test_truncated_length(self):
        with self.assertRaisesRegex(ProviderFailure,'TRUNCATED'):self.call(Response(headers={'Content-Length':'3'}))
    def test_bad_request_id(self):
        with self.assertRaisesRegex(ProviderFailure,'REQUEST_ID'):self.call(Response(headers={'request-id':'unsafe\nvalue'}))
    def test_network_error_is_redacted_not_retried(self):
        with patch('bie.audio.neural_transport.http.client.HTTPSConnection',side_effect=OSError('secret fake_test_key')):
            # Construction failures must also be redacted, not expose source/secrets.
            with self.assertRaisesRegex(ProviderFailure,'NETWORK_UNCONFIRMED'):_exchange('GET','/v1/models',b'','fake_test_key',10000,1)
        conn=Connection(Response());conn.request=lambda *a,**k:(_ for _ in ()).throw(OSError('fake_test_key'))
        with patch('bie.audio.neural_transport.http.client.HTTPSConnection',return_value=conn),self.assertRaises(ProviderFailure) as cm:
            _exchange('GET','/v1/models',b'','fake_test_key',10000,1)
        self.assertNotIn('fake_test_key',str(cm.exception));self.assertFalse(cm.exception.retryable)
    def test_credential_control_chars_block(self):
        with self.assertRaisesRegex(ProviderFailure,'CREDENTIAL'):_exchange('GET','/v1/models',b'','bad\nkey1',10000,1)
    def test_host_or_path_injection(self):
        for path in ['https://evil.test/','//evil.test','/v1/voices/../secret','/v1/models?redirect=x']:
            with self.subTest(path=path),self.assertRaises(ProviderFailure):_valid_call('GET',path,b'',1000,1)
    def test_unknown_pcm_not_sent(self):
        with self.assertRaises(ProviderFailure):_valid_call('POST','/v1/text-to-speech/a/with-timestamps?output_format=mp3_44100&enable_logging=true',b'{}',1000,1)
    def test_post_path_permitted(self):_valid_call('POST','/v1/text-to-speech/a/with-timestamps?output_format=pcm_24000&enable_logging=false',b'{}',1000,1)
    def test_cancel_before_process(self):
        c=Event();c.set()
        with self.assertRaisesRegex(ProviderFailure,'CANCELLED'):_bounded(sleeper,(1,),1,c,1024)
    def test_process_deadline_kills_worker(self):
        start=time.monotonic()
        with self.assertRaisesRegex(ProviderFailure,'DEADLINE'):_bounded(sleeper,(10,),.2,None,1024)
        self.assertLess(time.monotonic()-start,2)
    def test_process_cancellation_kills_worker(self):
        c=Event();timer=threading.Timer(.2,c.set);timer.start();self.addCleanup(timer.cancel);start=time.monotonic()
        with self.assertRaisesRegex(ProviderFailure,'CANCELLED'):_bounded(sleeper,(10,),5,c,1024)
        self.assertLess(time.monotonic()-start,2)
    def test_process_result(self):self.assertIn(b'fixture',_bounded(sleeper,(.01,),5,None,1024))
    def test_process_crash_no_success(self):
        with self.assertRaises(ProviderFailure):_bounded(die,(),5,None,1024)
    def test_packet_budget(self):
        with self.assertRaisesRegex(ProviderFailure,'PACKET'):_bounded(huge_packet,(),5,None,10)
    def test_deadline_bool_rejected(self):
        with self.assertRaises(ProviderFailure):OfficialNeuralTransport().request('GET','/v1/models',b'',api_key='fake_test_key',maximum=1000,deadline=True,socket_timeout=1)
