"""H5-003: manifest-only loopback HTTP server with bounded request accounting.
Only trusted local diagnostic assets. This is not a public deployment server.
"""
from contextlib import contextmanager
from http.server import HTTPServer,BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import hashlib, threading, time
from types import MappingProxyType
from .origin import request_path,headers,HEADERS
from ...models import BenchmarkError

class AssetServer(ThreadingMixIn,HTTPServer):
    daemon_threads=True;block_on_close=False;request_queue_size=8;allow_reuse_address=False
    def __init__(self,assets,*,max_requests,max_response_bytes):
        self.assets=MappingProxyType(dict(assets));self.records=[];self.record_limit=2000
        self.max_requests=max_requests;self.max_response_bytes=max_response_bytes
        self.requests=0;self.bytes_reserved=0;self.limit_exceeded=False
        self.lock=threading.Lock();self.slots=threading.BoundedSemaphore(8)
        self.condition=threading.Condition(self.lock);self.active_connections=0
        super().__init__(('127.0.0.1',0),Handler)
    @property
    def origin(self):return 'http://127.0.0.1:'+str(self.server_port)
    def get_request(self):
        sock,addr=super().get_request();sock.settimeout(1.0);return sock,addr
    def process_request(self,request,client_address):
        if not self.slots.acquire(blocking=False):
            with self.lock:self.limit_exceeded=True
            self.shutdown_request(request);return
        with self.condition:self.active_connections+=1
        try:super().process_request(request,client_address)
        except BaseException:
            self.finished();raise
    def finished(self):
        with self.condition:
            self.active_connections-=1;self.condition.notify_all()
        self.slots.release()
    def process_request_thread(self,request,client_address):
        try:super().process_request_thread(request,client_address)
        finally:self.finished()
    def handle_error(self,*args):
        with self.lock:self.limit_exceeded=True
    def reserve(self,size):
        with self.lock:
            self.requests+=1
            if self.requests>self.max_requests or self.bytes_reserved+size>self.max_response_bytes:
                self.limit_exceeded=True;return False
            self.bytes_reserved+=size;return True
    def log(self,row):
        with self.lock:
            if len(self.records)<self.record_limit:self.records.append(row)
            else:self.limit_exceeded=True
    def snapshot(self,*,quiesce_timeout=2.0):
        # Client reads can finish before the handler's finally/log block. Never
        # publish a transient transcript as complete. A stalled handler blocks
        # evidence collection with a bounded deadline instead of partial success.
        if type(quiesce_timeout) not in (int,float) or not 0<quiesce_timeout<=5:
            raise BenchmarkError('HTTP_SERVER_DRAIN_LIMIT_INVALID')
        deadline=time.monotonic()+quiesce_timeout
        with self.condition:
            while self.active_connections:
                remaining=deadline-time.monotonic()
                if remaining<=0:raise BenchmarkError('HTTP_SERVER_DRAIN_TIMEOUT')
                self.condition.wait(remaining)
            return {'records':list(self.records),'requests':self.requests,
                    'response_bytes_reserved':self.bytes_reserved,'limit_exceeded':self.limit_exceeded}

class Handler(BaseHTTPRequestHandler):
    protocol_version='HTTP/1.0';server_version='BIE-Local-Diagnostic';sys_version=''
    def log_message(self,*a):pass
    def do_GET(self):self.respond(send_body=True)
    def do_HEAD(self):self.respond(send_body=False)
    def do_POST(self):self.respond(send_body=False,deny=True)
    do_PUT=do_POST;do_DELETE=do_POST;do_OPTIONS=do_POST;do_CONNECT=do_POST;do_PATCH=do_POST
    def respond(self,send_body,deny=False):
        self.close_connection=True;status=200;name=None;body=b'';mime=None
        try:
            # One exact Host; reject DNS rebinding, origin-form confusion, and bodies.
            if self.headers.get_all('Host')!=['127.0.0.1:'+str(self.server.server_port)]:
                raise BenchmarkError('HTTP_HOST_DENIED')
            if self.headers.get('Transfer-Encoding') is not None or self.headers.get('Content-Length') not in (None,'0'):
                raise BenchmarkError('HTTP_BODY_DENIED')
            if deny:status=405
            else:
                name=request_path(self.path)
                if name not in self.server.assets:status=404
                else:body=self.server.assets[name]
        except BenchmarkError:status=400
        size=len(body) if status==200 and send_body else 0
        if not self.server.reserve(size):status=429;body=b'';size=0
        h=headers(name,body) if status==200 else {**HEADERS,'Content-Type':'text/plain','Content-Length':'0'}
        sent=False
        try:
            self.send_response(status)
            for k,v in h.items():self.send_header(k,v)
            self.send_header('Connection','close');self.end_headers()
            if send_body and status==200:self.wfile.write(body);self.wfile.flush()
            sent=True
        except (OSError,TimeoutError):pass
        finally:
            self.server.log({'method':self.command,'path':name,'status':status,'size_bytes':size,
                'sha256':hashlib.sha256(body).hexdigest() if status==200 else None,
                'response_completed':sent,'headers':h})

@contextmanager
def serve(assets,*,max_requests=200,max_response_bytes=32_000_000):
    if type(assets) is not dict or not assets or any(type(k) is not str or type(v) is not bytes for k,v in assets.items()):
        raise BenchmarkError('HTTP_ASSETS_INVALID')
    for k in assets:request_path('/'+k)
    if type(max_requests) is not int or not 1<=max_requests<=2000 or type(max_response_bytes) is not int or not 1<=max_response_bytes<=256_000_000:
        raise BenchmarkError('HTTP_SERVER_LIMIT_INVALID')
    server=AssetServer(assets,max_requests=max_requests,max_response_bytes=max_response_bytes)
    thread=threading.Thread(target=server.serve_forever,kwargs={'poll_interval':0.05},daemon=True);thread.start()
    try:yield server
    finally:server.shutdown();server.server_close();thread.join(timeout=2)
