"""H1: runnable neural adapter over existing SpeechProvider contracts.

No test-double output may carry this adapter's production provider identity.
Remote model/voice metadata is pinned per deployment, not immutable model weights.
Live synthesis is explicit opt-in and never silently falls back to local eSpeak.
"""
from __future__ import annotations
from threading import Event
from dataclasses import asdict
import hashlib, time
from .common import AudioError, fingerprint, strict_json
from .tts_contract import ProviderAudio, ProviderFailure
from .neural_policy import NeuralDeployment, PROVIDER, FIXTURE_PROVIDER, neural_catalog, request_payload, identifier
from .neural_transport import OfficialNeuralTransport, HTTPReply
from .neural_store import NeuralResponseStore, canonical
from .neural_response import decode_response, bind_neural_alignment
from .neural_authority import LiveProviderAuthority
from .neural_call_journal import PaidCallJournal
from .neural_scheduler import ProviderCallScheduler


class ElevenLabsProvider:
    def __init__(self,config,store,*,api_key=None,allow_live=False,transport=None,fixture=False,context_plan=None,authority=None,journal=None,scheduler=None):
        if type(config)is not NeuralDeployment or type(store)is not NeuralResponseStore:
            raise AudioError('NEURAL_TYPED_CONFIGURATION_REQUIRED')
        if type(allow_live)is not bool or type(fixture)is not bool:raise AudioError('NEURAL_POLICY_BOOLEAN')
        transport=transport or OfficialNeuralTransport()
        if not fixture and type(transport)is not OfficialNeuralTransport:raise AudioError('NEURAL_TRANSPORT_AUTHORITY')
        if fixture and (type(transport)is OfficialNeuralTransport or getattr(transport,'evidence_scope',None)!='CONTRACT_FIXTURE'):
            raise AudioError('NEURAL_FIXTURE_SCOPE_REQUIRED')
        if fixture and (allow_live or api_key or authority or journal or scheduler):raise AudioError('NEURAL_FIXTURE_MUST_NOT_HAVE_LIVE_CREDENTIALS')
        if not fixture and api_key is not None:raise AudioError('NEURAL_DIRECT_SECRET_INJECTION_DISABLED')
        if not fixture and allow_live and (type(authority)is not LiveProviderAuthority or type(journal)is not PaidCallJournal or type(scheduler)is not ProviderCallScheduler):
            raise AudioError('NEURAL_LIVE_CONTROL_REQUIRED')
        self.config=config;self.store=store;self.allow_live=allow_live;self.transport=transport;self.fixture=fixture
        self.authority=authority;self.journal=journal;self.scheduler=scheduler
        self.provider_id=FIXTURE_PROVIDER if fixture else PROVIDER
        self._context_plan=context_plan
        self._catalog=neural_catalog(config,fixture=fixture,context_fingerprint=context_plan.fingerprint() if context_plan else None)
        self.request_count=0;self.generation_count=0;self.cache_responses=0
    def __repr__(self):return f'ElevenLabsProvider(provider_id={self.provider_id!r}, credentials=<redacted>)'
    def catalog(self):
        current=neural_catalog(self.config,fixture=self.fixture,context_fingerprint=self._context_plan.fingerprint() if self._context_plan else None)
        if current!=self._catalog:raise ProviderFailure('PROVIDER_CONFIGURATION_CHANGED')
        return self._catalog
    def _context(self,request):
        if self._context_plan is None:return None
        plan=self._context_plan
        if request.plan_fingerprint!=plan.fingerprint():raise AudioError('NEURAL_CONTEXT_PLAN_CHANGED')
        found=[i for i,s in enumerate(plan.segments) if s==request.segment]
        if len(found)!=1:raise AudioError('NEURAL_CONTEXT_SEGMENT_CHANGED')
        i=found[0];out={}
        for key,j in (('previous_text',i-1),('next_text',i+1)):
            if 0<=j<len(plan.segments):
                neighbor=plan.segments[j]
                if neighbor.scene_id==request.segment.scene_id and neighbor.persona_id==request.segment.persona_id:
                    out[key]=neighbor.spoken_text
        return out
    def _payload(self,request):
        self.catalog()
        if request.voice not in self._catalog.voices or request.catalog_fingerprint!=self._catalog.fingerprint():
            raise ProviderFailure('PROVIDER_CATALOG_CHANGED')
        return canonical(request_payload(request,self.config,context=self._context(request)))
    def preflight(self,requests):
        rows=tuple(requests)
        if self.fixture:return {'calls':len(rows),'characters':sum(len(r.segment.spoken_text) for r in rows),'truncated':False}
        if self.allow_live and type(self.authority)is not LiveProviderAuthority:raise ProviderFailure('NEURAL_LIVE_CONTROL_REQUIRED')
        return self.authority.preflight(rows) if self.authority is not None else {'calls':len(rows),'characters':sum(len(r.segment.spoken_text) for r in rows),'truncated':False}
    def _permission(self,method,path,*,text_chars=0):
        if self.fixture:return None
        if not self.allow_live:raise ProviderFailure('NEURAL_LIVE_OPT_IN_REQUIRED')
        if not self.config.provider_data_transfer_approved:raise ProviderFailure('NEURAL_DATA_TRANSFER_NOT_APPROVED')
        if type(self.authority)is not LiveProviderAuthority:raise ProviderFailure('NEURAL_LIVE_CONTROL_REQUIRED')
        return self.authority.authorize(method,path,text_chars=text_chars)
    def _http(self,method,path,payload,cancel,start,*,text_chars=0):
        if (not self.fixture and type(self.transport)is not OfficialNeuralTransport) or (self.fixture and getattr(self.transport,'evidence_scope',None)!='CONTRACT_FIXTURE'):
            raise ProviderFailure('NEURAL_TRANSPORT_AUTHORITY')
        api_key=self._permission(method,path,text_chars=text_chars)
        if cancel.is_set():raise ProviderFailure('CANCELLED')
        remaining=self.config.deadline_seconds-(time.monotonic()-start)
        if remaining<=0:raise ProviderFailure('NEURAL_DEADLINE_REMOTE_COMPLETION_UNCONFIRMED')
        self.request_count+=1
        reply=self.transport.request(method,path,payload,api_key=api_key,maximum=self.config.max_response_bytes,
                   deadline=remaining,socket_timeout=min(remaining,self.config.socket_timeout_seconds),cancellation=cancel)
        if time.monotonic()-start>=self.config.deadline_seconds:raise ProviderFailure('NEURAL_DEADLINE_REMOTE_COMPLETION_UNCONFIRMED')
        if cancel.is_set():raise ProviderFailure('CANCELLED_REMOTE_COMPLETION_UNCONFIRMED')
        expected_scope='CONTRACT_FIXTURE' if self.fixture else 'OFFICIAL_HTTPS_RESPONSE'
        if type(reply)is not HTTPReply or reply.evidence_scope!=expected_scope or type(reply.body)is not bytes or len(reply.body)>self.config.max_response_bytes:
            raise ProviderFailure('NEURAL_TRANSPORT_SCOPE_MISMATCH')
        if type(reply.status)is not int:raise ProviderFailure('NEURAL_HTTP_STATUS_INVALID')
        if reply.status!=200:
            # No server error text, possible source echoes or credential values exposed.
            code={401:'NEURAL_AUTH_REJECTED',403:'NEURAL_PERMISSION_OR_PLAN_REJECTED',429:'NEURAL_RATE_LIMIT'}.get(reply.status,'NEURAL_HTTP_FAILURE')
            raise ProviderFailure(code,retryable=False)
        return reply
    def _remote_identity(self,request,cancel,start):
        models=self._http('GET','/v1/models',b'',cancel,start,text_chars=0)
        voice=self._http('GET','/v1/voices/'+self.config.voice_id,b'',cancel,start,text_chars=0)
        try:
            items=strict_json(models.body.decode());v=strict_json(voice.body.decode())
            if type(items)is not list or len(items)>1000:raise ValueError()
            rows=[r for r in items if type(r)is dict and r.get('model_id')==self.config.model_id]
            if len(rows)!=1 or type(v)is not dict or v.get('voice_id')!=self.config.voice_id:raise ValueError()
            m=rows[0]
            if m.get('can_do_text_to_speech')is not True:raise ValueError()
            if self.config.settings.style != 0 and m.get('can_use_style') is not True:
                raise ProviderFailure('NEURAL_STYLE_CAPABILITY_MISMATCH')
            if self.config.settings.use_speaker_boost and m.get('can_use_speaker_boost') is not True:
                raise ProviderFailure('NEURAL_SPEAKER_BOOST_CAPABILITY_MISMATCH')
            languages=m.get('languages')
            if type(languages)is not list or self.config.primary_language not in [x.get('language_id') for x in languages if type(x)is dict]:raise ValueError()
            if fingerprint(m)!=self.config.model_metadata_fingerprint or fingerprint(v)!=self.config.voice_metadata_fingerprint:
                raise ProviderFailure('NEURAL_METADATA_DRIFT_REAPPROVAL_REQUIRED')
            maximum=m.get('maximum_text_length_per_request')
            if maximum is not None and (type(maximum)is not int or len(request.segment.spoken_text)>maximum):raise ValueError()
        except ProviderFailure:raise
        except (ValueError,TypeError,UnicodeError):raise ProviderFailure('NEURAL_REMOTE_CAPABILITY_MISMATCH') from None
    def _reply(self,request,*,cancellation=None,network=True):
        cancel=cancellation or Event();payload=self._payload(request);ph=hashlib.sha256(payload).hexdigest()
        scope='CONTRACT_FIXTURE' if self.fixture else 'OFFICIAL_HTTPS_RESPONSE'
        with self.store.lock(request,timeout=self.config.deadline_seconds,cancellation=cancel):
            if cancel.is_set():raise ProviderFailure('CANCELLED')
            reply=self.store.load(request,payload_hash=ph,scope=scope,maximum=self.config.max_response_bytes)
            if reply is not None:
                decoded=decode_response(reply,request,max_bytes=self.config.max_response_bytes);self.cache_responses+=1
                if not self.fixture and self.journal is not None:
                    self.journal.reconcile_cached(request_fingerprint=request.fingerprint(),deployment_fingerprint=self.config.fingerprint(),
                        payload_sha256=ph,provider_request_id=reply.request_id,response_sha256=hashlib.sha256(reply.body).hexdigest())
                return reply,decoded
            if not network:raise AudioError('NEURAL_TIMING_RESPONSE_MISSING_NO_RESYNTHESIS')
            start=time.monotonic();self._remote_identity(request,cancel,start)
            path=f'/v1/text-to-speech/{self.config.voice_id}/with-timestamps?output_format=pcm_{self.config.sample_rate}&enable_logging={str(self.config.enable_provider_logging).lower()}'
            if self.fixture:
                self.generation_count+=1
                reply=self._http('POST',path,payload,cancel,start,text_chars=len(request.segment.spoken_text))
            else:
                if type(self.journal)is not PaidCallJournal or type(self.scheduler)is not ProviderCallScheduler:
                    raise ProviderFailure('NEURAL_LIVE_CONTROL_REQUIRED')
                ticket=self.journal.prepare(request_fingerprint=request.fingerprint(),deployment_fingerprint=self.config.fingerprint(),payload_sha256=ph)
                with self.scheduler.acquire(ticket.call_key,cancellation=cancel):
                    if cancel.is_set():raise ProviderFailure('CANCELLED')
                    self.journal.mark_in_flight(ticket);self.generation_count+=1
                    try:
                        reply=self._http('POST',path,payload,cancel,start,text_chars=len(request.segment.spoken_text))
                    except ProviderFailure as exc:
                        if exc.code in ('NEURAL_AUTH_REJECTED','NEURAL_PERMISSION_OR_PLAN_REJECTED','NEURAL_RATE_LIMIT','NEURAL_HTTP_FAILURE'):
                            status={'NEURAL_AUTH_REJECTED':401,'NEURAL_PERMISSION_OR_PLAN_REJECTED':403,'NEURAL_RATE_LIMIT':429}.get(exc.code)
                            self.journal.mark_rejected(ticket,http_status=status)
                        else:
                            self.journal.mark_uncertain(ticket)
                        raise
                    if not reply.request_id:
                        self.journal.mark_uncertain(ticket);raise ProviderFailure('NEURAL_PROVIDER_REQUEST_ID_MISSING')
                    identifier(reply.request_id.replace('-','_').replace(':','_').replace('.','_'),'request id')
                    self.journal.mark_confirmed(ticket,provider_request_id=reply.request_id,response_sha256=hashlib.sha256(reply.body).hexdigest())
            if not reply.request_id:raise ProviderFailure('NEURAL_PROVIDER_REQUEST_ID_MISSING')
            identifier(reply.request_id.replace('-','_').replace(':','_').replace('.','_'),'request id')
            decoded=decode_response(reply,request,max_bytes=self.config.max_response_bytes)
            if cancel.is_set():raise ProviderFailure('CANCELLED_REMOTE_COMPLETION_UNCONFIRMED')
            self.store.put(request,reply,payload_hash=ph)
            return reply,decoded
    def synthesize(self,request,*,cancellation=None):
        reply,decoded=self._reply(request,cancellation=cancellation)
        return ProviderAudio(request.fingerprint(),self.provider_id,request.voice.fingerprint(),request.voice.runtime_fingerprint,
              decoded.wav_bytes,reply.request_id,('CONTRACT_FIXTURE_NOT_NEURAL_SPEECH',) if self.fixture else
              ('REMOTE_MODEL_ALIAS_NOT_WEIGHT_PIN','PROVIDER_TIMINGS_NOT_INDEPENDENT_ACOUSTIC_ALIGNMENT','NEURAL_LISTENING_ACCEPTANCE_PENDING',
               'LANGUAGE_MODE_'+self.config.language_mode.upper()))
    def alignment_for(self,asset,*,cancellation=None):
        reply,decoded=self._reply(asset.request,cancellation=cancellation,network=False)
        if reply.request_id!=asset.invocation_id:raise AudioError('NEURAL_TIMING_INVOCATION_CHANGED')
        alignment=bind_neural_alignment(asset,decoded,producer_fingerprint=fingerprint(('neural-provider-character-adoption/1',self.config.fingerprint())),
                                        request_id=reply.request_id,fixture=self.fixture)
        evidence={'schema_version':'bie.audio.neural-response-evidence/1','provider_id':self.provider_id,
            'scope':reply.evidence_scope,'request_fingerprint':asset.request.fingerprint(),'response_sha256':decoded.response_sha256,
            'provider_request_id':reply.request_id,'rights_refs':list(self.config.rights_refs),
            'provider_model_weights_pinned':False,'provider_signature_verified':False,'local_seal_checked':True,
            'acoustic_alignment_verified':False,'cinematic_quality_verified':False,'product_accepted':False,
            'live_authority_fingerprint':None if self.fixture or self.authority is None else self.authority.policy.fingerprint()}
        return alignment,evidence
