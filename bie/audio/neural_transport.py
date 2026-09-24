"""H1-002: official-origin HTTPS with a killable bounded child process.

Credentials are passed in memory, never command arguments, files or diagnostics.
No automatic retries: an interrupted POST may already have been billed remotely.
This process timeout is not canonical BIE kernel-worker/CAS adoption (F03).
"""
from __future__ import annotations
from dataclasses import dataclass
from threading import Event
import http.client, ssl, re, json, time, multiprocessing, os, socket
from .tts_contract import ProviderFailure

@dataclass(frozen=True)
class HTTPReply:
    status: int
    body: bytes
    request_id: str
    evidence_scope: str = 'OFFICIAL_HTTPS_RESPONSE'


def _valid_call(method, path, body, maximum, timeout):
    ok = method == 'GET' and (path == '/v1/models' or re.fullmatch(r'/v1/voices/[A-Za-z0-9_-]{1,128}', path))
    ok = ok or (method == 'POST' and re.fullmatch(r'/v1/text-to-speech/[A-Za-z0-9_-]{1,128}/with-timestamps\?output_format=pcm_(16000|22050|24000)&enable_logging=(true|false)', path))
    if not ok or type(body) is not bytes or len(body)>100000 or (method=='GET' and body):
        raise ProviderFailure('NEURAL_HTTP_REQUEST_POLICY')
    if type(maximum) is not int or not 1 <= maximum <= 7_500_000 or type(timeout) not in (int,float) or not 0 < timeout <= 180:
        raise ProviderFailure('NEURAL_HTTP_LIMIT_POLICY')


def _exchange(method, path, body, api_key, maximum, socket_timeout):
    _valid_call(method,path,body,maximum,socket_timeout)
    if type(api_key) is not str or not re.fullmatch(r'[A-Za-z0-9_-]{8,512}', api_key):
        raise ProviderFailure('NEURAL_CREDENTIAL_INVALID')
    conn = None
    try:
        conn = http.client.HTTPSConnection('api.elevenlabs.io', 443, timeout=socket_timeout,
                                          context=ssl.create_default_context())
        conn.request(method,path,body=body or None,headers={'xi-api-key':api_key,'Accept':'application/json',
                    'Content-Type':'application/json','Accept-Encoding':'identity','User-Agent':'BIE-AUDIO-H1/1'})
        response = conn.getresponse()
        # Never follow redirects or pass a secret to a new origin.
        if 300 <= response.status < 400: raise ProviderFailure('NEURAL_REDIRECT_REJECTED')
        if response.getheader('Content-Encoding','identity').lower() != 'identity':
            raise ProviderFailure('NEURAL_COMPRESSED_RESPONSE_REJECTED')
        declared=response.getheader('Content-Length')
        if declared is not None and (not declared.isdigit() or int(declared)>maximum):
            raise ProviderFailure('NEURAL_RESPONSE_BUDGET')
        if response.getheader('Content-Type','').split(';')[0].strip().lower() != 'application/json':
            raise ProviderFailure('NEURAL_RESPONSE_CONTENT_TYPE')
        chunks=[]; size=0
        while True:
            part=response.read(min(65536,maximum-size+1))
            if not part: break
            size+=len(part)
            if size>maximum: raise ProviderFailure('NEURAL_RESPONSE_BUDGET')
            chunks.append(part)
        if declared is not None and size!=int(declared): raise ProviderFailure('NEURAL_RESPONSE_TRUNCATED')
        rid=response.getheader('request-id') or response.getheader('x-request-id') or ''
        if rid and not re.fullmatch(r'[A-Za-z0-9_.:-]{1,256}',rid): raise ProviderFailure('NEURAL_REQUEST_ID_INVALID')
        return HTTPReply(response.status,b''.join(chunks),rid)
    except ProviderFailure: raise
    except (OSError,ssl.SSLError,http.client.HTTPException):
        # Do not surface server text, source narration, URLs or exception locals.
        raise ProviderFailure('NEURAL_NETWORK_UNCONFIRMED',retryable=False) from None
    finally:
        if conn is not None: conn.close()


def _worker(send, args):
    try:
        reply=_exchange(*args)
        metadata=json.dumps({'status':reply.status,'request_id':reply.request_id}).encode()
        send.send_bytes(metadata+b'\n'+reply.body)
    except ProviderFailure as e:
        send.send_bytes(json.dumps({'error':e.code}).encode()+b'\n')
    except Exception:
        send.send_bytes(b'{"error":"NEURAL_TRANSPORT_WORKER_FAILED"}\n')
    finally: send.close()


def _bounded(worker, args, deadline, cancellation, maximum):
    """Private primitive. Production callers always select the fixed _worker."""
    cancel=cancellation or Event()
    if cancel.is_set(): raise ProviderFailure('CANCELLED')
    ctx=multiprocessing.get_context('spawn');receive,send=ctx.Pipe(duplex=False)
    process=ctx.Process(target=worker,args=(send,args),daemon=True)
    start=time.monotonic()
    try:
        process.start();send.close()
        while True:
            if cancel.is_set(): raise ProviderFailure('CANCELLED_REMOTE_COMPLETION_UNCONFIRMED')
            remaining=deadline-(time.monotonic()-start)
            if remaining<=0: raise ProviderFailure('NEURAL_DEADLINE_REMOTE_COMPLETION_UNCONFIRMED')
            if receive.poll(min(.02,remaining)):
                try: packet=receive.recv_bytes(maximum+2048)
                except (EOFError,OSError): raise ProviderFailure('NEURAL_TRANSPORT_PACKET_INVALID') from None
                if time.monotonic()-start>=deadline: raise ProviderFailure('NEURAL_DEADLINE_REMOTE_COMPLETION_UNCONFIRMED')
                if cancel.is_set(): raise ProviderFailure('CANCELLED_REMOTE_COMPLETION_UNCONFIRMED')
                return packet
            if not process.is_alive(): raise ProviderFailure('NEURAL_TRANSPORT_WORKER_EXIT')
    finally:
        receive.close();send.close()
        if process.pid is not None:
            if process.is_alive(): process.terminate()
            process.join(timeout=.5)
            if process.is_alive(): process.kill();process.join(timeout=.5)
            process.close()


class OfficialNeuralTransport:
    evidence_scope='OFFICIAL_HTTPS_RESPONSE'
    def request(self,method,path,body,*,api_key,maximum,deadline,socket_timeout,cancellation=None):
        _valid_call(method,path,body,maximum,socket_timeout)
        if type(deadline) not in (float,int) or not .01<=deadline<=180:
            raise ProviderFailure('NEURAL_HTTP_LIMIT_POLICY')
        packet=_bounded(_worker,(method,path,body,api_key,maximum,min(socket_timeout,deadline)),deadline,cancellation,maximum)
        try:
            header,raw=packet.split(b'\n',1);meta=json.loads(header)
            if set(meta)=={'error'}:
                code=meta['error']
                if type(code)is not str or not re.fullmatch('[A-Z_]{1,100}',code): raise ValueError()
                raise ProviderFailure(code,retryable=False)
            if set(meta)!={'status','request_id'} or type(meta['status'])is not int or not 100<=meta['status']<=599 or len(raw)>maximum:
                raise ValueError()
            return HTTPReply(meta['status'],raw,meta['request_id'])
        except ProviderFailure: raise
        except (ValueError,TypeError): raise ProviderFailure('NEURAL_TRANSPORT_PACKET_INVALID') from None
