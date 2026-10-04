"""Actual local control-plane adapters, not a provider/worker/queue replacement.

Provider adapters and health observations are trusted process ports only. No
provider is invented, probed or invoked here. Persisted configuration is not a
claim that its adapter is provisioned in every process. Queue GETs are read-only;
failed PDF parents can only spawn a governed retry, not unsafe state redrive.
"""
from dataclasses import replace
import hashlib,json,math,time,uuid
from bie.model_gateway.provider_registry import ProviderRegistry,ProviderDescriptor
from bie.model_gateway.capability_taxonomy import validate_capabilities
from bie.model_gateway.availability import Health,usable
from bie.infrastructure.worker_health import WorkerHeartbeat,classify as worker_health
from bie.infrastructure.worker_scheduler import WorkerCapabilities
from bie.infrastructure.durable_task_queue import VALID_STATES
from apps.api.job_service import STAGE_ID,CAPABILITY
from .contracts import require,ident,digest,canonical,HASH,OperatorError
from .catalog import timestamp

ORIGINS=('SYNTHETIC_TEST','NATIVE_OBSERVATION')
EVENTS={'ENQUEUED','DELIVERED','ACKED','NACKED','DEAD_LETTERED','REDRIVEN','VISIBILITY_RECOVERED'}
REASONS={'source_stored','delivered','enqueued','acked','operator_cancelled','pdf_inspection_failed',
         'internal_worker_error','visibility timeout','visibility timeout: max deliveries exceeded','manual redrive'}

def number(v,code='admin_numeric_invalid',minimum=0,maximum=1e12):
    require(type(v) in (int,float) and math.isfinite(v) and minimum<=v<=maximum,code)
    return v

def count(v,maximum=10000):
    require(type(v) is int and 0<=v<=maximum,'admin_count_invalid');return v

def page(after,limit):
    if after is not None:ident(after)
    require(type(limit) is int and 1<=limit<=50,'invalid_pagination',400)

def safe_reason(raw):
    require(type(raw) is str and len(raw)<=4096,'queue_reason_invalid')
    return dict(reason_code=raw if raw in REASONS else 'diagnostic_redacted',
                reason_sha256=hashlib.sha256(raw.encode()).hexdigest(),reason_char_count=len(raw))

class Administration:
    def __init__(self,service):
        self.s=service;self.bindings={};self.health={}

    def _auth(self,p,permission='admin_read'):self.s.authorize(p,permission)

    def provision_provider(self,p,descriptor,adapter,*,secret_reference=None,evidence_origin):
        """Trusted provisioning, not an HTTP plugin loader or credential reader."""
        self._auth(p,'admin_config')
        require(type(descriptor) is ProviderDescriptor,'provider_descriptor_invalid')
        ident(descriptor.provider_id);ident(descriptor.model_id)
        require(type(descriptor.enabled) is bool and type(descriptor.capabilities) is frozenset,
                'provider_descriptor_invalid')
        try:capabilities=validate_capabilities(descriptor.capabilities)
        except ValueError:raise OperatorError('provider_capabilities_invalid',400) from None
        require(callable(getattr(adapter,'invoke',None)),'provider_adapter_invalid')
        require(evidence_origin in ORIGINS,'admin_origin_invalid',400)
        require(1<=len(capabilities)<=9,'provider_capabilities_invalid',400)
        if secret_reference is not None:
            require(type(secret_reference) is str and secret_reference.startswith('secretref-') and
                    HASH.fullmatch(secret_reference[10:]),'secret_reference_invalid',400)
        config_id='provider-'+digest(dict(provider=descriptor.provider_id,model=descriptor.model_id))
        value=dict(provider_id=descriptor.provider_id,model_id=descriptor.model_id,capabilities=sorted(capabilities),
                   secret_reference=secret_reference,enabled=descriptor.enabled,evidence_origin=evidence_origin)
        # Exercise the existing canonical registration contract, not a substitute.
        registry=ProviderRegistry();registry.register(descriptor,adapter)
        with self.s.catalog.tx() as db:
            old=db.execute('SELECT body FROM provider_versions WHERE tenant=? AND id=? ORDER BY revision DESC LIMIT 1',
                           (p.tenant,config_id)).fetchone()
            if old:
                body=json.loads(old[0]);require(body['configuration']==value,'provider_provisioning_conflict')
            else:
                require(db.execute('SELECT COUNT(DISTINCT id) FROM provider_versions WHERE tenant=?',(p.tenant,)).fetchone()[0]<128,
                        'provider_limit',429)
                body=dict(configuration=value,configuration_sha256=digest(value),revision=1,activated_at=timestamp(),
                          request_fingerprint=None,request_key_hash=None)
                db.execute('INSERT INTO provider_versions VALUES(?,?,?,?)',(p.tenant,config_id,1,canonical(body).decode()))
                self.s.catalog.event(db,p.actor,'PROVIDER_PROVISIONED',config_id,
                                     dict(configuration_sha256=body['configuration_sha256'],revision=1))
        self.bindings[(p.tenant,config_id)]=(descriptor,adapter,secret_reference)
        return config_id

    def bind_provider(self,p,config_id,descriptor,adapter,*,secret_reference=None):
        """Rebind a persisted approved adapter after restart; never deserialize it."""
        self._auth(p,'admin_config');ident(config_id)
        with self.s.catalog.tx(read_only=True) as db:body=self._provider(db,p,config_id)
        cfg=body['configuration']
        require(type(descriptor) is ProviderDescriptor and descriptor.provider_id==cfg['provider_id'] and
                descriptor.model_id==cfg['model_id'] and sorted(descriptor.capabilities)==cfg['capabilities'] and
                secret_reference==cfg['secret_reference'] and callable(getattr(adapter,'invoke',None)),
                'provider_binding_mismatch')
        registry=ProviderRegistry();registry.register(replace(descriptor,enabled=cfg['enabled']),adapter)
        self.bindings[(p.tenant,config_id)]=(descriptor,adapter,secret_reference)

    def _provider(self,db,p,config_id,revision=None):
        if revision is not None:
            require(type(revision) is int and revision>=1,'invalid_revision',400)
            row=db.execute('SELECT body FROM provider_versions WHERE tenant=? AND id=? AND revision=?',
                           (p.tenant,config_id,revision)).fetchone()
        else:
            row=db.execute('SELECT body FROM provider_versions WHERE tenant=? AND id=? ORDER BY revision DESC LIMIT 1',
                           (p.tenant,config_id)).fetchone()
        require(row is not None,'provider_not_found',404);body=json.loads(row[0])
        require(digest(body['configuration'])==body['configuration_sha256'],'provider_configuration_tampered')
        return body

    def runtime_registry(self,p):
        self._auth(p);registry=ProviderRegistry()
        with self.s.catalog.tx(read_only=True) as db:
            rows=db.execute('SELECT DISTINCT id FROM provider_versions WHERE tenant=? ORDER BY id',(p.tenant,)).fetchall()
            require(len(rows)<=128,'provider_limit')
            for row in rows:
                body=self._provider(db,p,row[0]);binding=self.bindings.get((p.tenant,row[0]))
                if binding:
                    descriptor,adapter,reference=binding;cfg=body['configuration']
                    require(descriptor.provider_id==cfg['provider_id'] and descriptor.model_id==cfg['model_id'] and
                            sorted(descriptor.capabilities)==cfg['capabilities'] and reference==cfg['secret_reference'],
                            'provider_binding_mismatch')
                    registry.register(replace(descriptor,enabled=cfg['enabled']),adapter)
        return registry

    def observe_provider_health(self,p,config_id,health,*,configuration_sha256,evidence_origin):
        self._auth(p,'admin_config');ident(config_id)
        require(type(health) is Health and type(health.available) is bool and evidence_origin in ORIGINS,
                'provider_health_invalid')
        number(health.latency_ms,maximum=120000);number(health.checked_at)
        require(health.checked_at<=time.time()+5,'provider_health_future')
        with self.s.catalog.tx(read_only=True) as db:body=self._provider(db,p,config_id)
        cfg=body['configuration']
        require(health.provider==cfg['provider_id'] and health.model==cfg['model_id'] and
                configuration_sha256==body['configuration_sha256'],'provider_health_binding')
        require(not(cfg['evidence_origin']=='SYNTHETIC_TEST' and evidence_origin=='NATIVE_OBSERVATION'),
                'admin_origin_promotion')
        usable(health)
        self.health[(p.tenant,config_id)]=(health,configuration_sha256,evidence_origin)

    def providers(self,p,after=None,limit=25):
        self._auth(p);page(after,limit);now=time.time();items=[]
        with self.s.catalog.tx(read_only=True) as db:
            rows=db.execute('SELECT DISTINCT id FROM provider_versions WHERE tenant=? AND id>? ORDER BY id LIMIT ?',
                            (p.tenant,after or '',limit+1)).fetchall()
            for row in rows[:limit]:
                config_id=row[0];body=self._provider(db,p,config_id);cfg=body['configuration']
                binding=self.bindings.get((p.tenant,config_id));health=self.health.get((p.tenant,config_id))
                reason='health_not_observed';state='NOT_RUN';available=False;checked_at=None
                if not binding:reason='adapter_not_bound_in_this_process'
                elif not cfg['enabled']:reason='provider_disabled';state='DISABLED'
                elif health:
                    h,sha,origin=health;checked_at=h.checked_at
                    if sha!=body['configuration_sha256']:reason='health_configuration_changed';state='STALE'
                    elif now-h.checked_at>60:reason='health_expired';state='STALE'
                    else:available=usable(h);state='AVAILABLE' if available else 'UNAVAILABLE';reason='observed_health'
                items.append(dict(config_id=config_id,revision=body['revision'],configuration_sha256=body['configuration_sha256'],
                    provider_id=cfg['provider_id'],model_id=cfg['model_id'],capabilities=cfg['capabilities'],enabled=cfg['enabled'],
                    bound_in_this_process=binding is not None,secret_reference=cfg['secret_reference'],secret_values_exposed=False,
                    health_status=state,health_reason=reason,health_available=available,health_checked_at=checked_at,
                    health_origin=health[2] if health else None,evidence_origin=cfg['evidence_origin'],
                    live_probe_performed=False,generation_enabled_for_inspection_profile=False,product_accepted=False))
        self.runtime_registry(p) # Enforce actual descriptor binding before exposing success.
        return dict(status='AVAILABLE' if items else 'NOT_CONFIGURED',items=items,
                    next_after=items[-1]['config_id'] if len(rows)>limit else None,
                    can_configure='admin_config' in p.permissions,live_calls_performed=False,product_accepted=False)

    def set_provider_enabled(self,p,config_id,enabled,expected_revision,key):
        self._auth(p,'admin_config');ident(config_id);ident(key)
        require(type(enabled) is bool and type(expected_revision) is int and expected_revision>=1,'invalid_provider_update',400)
        fingerprint=digest(dict(id=config_id,enabled=enabled,expected_revision=expected_revision))
        key_hash=digest(dict(tenant=p.tenant,action='provider_enable',id=config_id,key=key))
        with self.s.catalog.tx() as db:
            current=self._provider(db,p,config_id)
            previous=db.execute('SELECT body FROM provider_versions WHERE tenant=? AND id=? ORDER BY revision',
                                (p.tenant,config_id)).fetchall()
            for row in previous:
                body=json.loads(row[0])
                if body['request_key_hash']==key_hash:
                    require(body['request_fingerprint']==fingerprint,'idempotency_conflict')
                    return dict(config_id=config_id,revision=body['revision'],configuration_sha256=body['configuration_sha256'],replayed=True)
            require(len(previous)<256,'provider_version_limit',429)
            require(current['revision']==expected_revision,'stale_revision')
            if enabled:require((p.tenant,config_id) in self.bindings,'provider_adapter_not_bound')
            cfg=dict(current['configuration'],enabled=enabled);revision=expected_revision+1
            body=dict(configuration=cfg,configuration_sha256=digest(cfg),revision=revision,activated_at=timestamp(),
                      request_fingerprint=fingerprint,request_key_hash=key_hash)
            db.execute('INSERT INTO provider_versions VALUES(?,?,?,?)',(p.tenant,config_id,revision,canonical(body).decode()))
            self.s.catalog.event(db,p.actor,'PROVIDER_CONFIGURATION_CHANGED',config_id,
                                 dict(before_hash=current['configuration_sha256'],after_hash=body['configuration_sha256'],revision=revision))
        return dict(config_id=config_id,revision=revision,configuration_sha256=body['configuration_sha256'],replayed=False)

    def provider_history(self,p,config_id,after_revision=0,limit=25):
        self._auth(p);ident(config_id);count(after_revision,256);page(None,limit)
        with self.s.catalog.tx(read_only=True) as db:
            self._provider(db,p,config_id)
            rows=db.execute('SELECT revision,body FROM provider_versions WHERE tenant=? AND id=? AND revision>? ORDER BY revision LIMIT ?',
                            (p.tenant,config_id,after_revision,limit+1)).fetchall()
            items=[dict(revision=r[0],configuration_sha256=json.loads(r[1])['configuration_sha256'],
                        configuration=json.loads(r[1])['configuration'],activated_at=json.loads(r[1])['activated_at']) for r in rows[:limit]]
        return dict(config_id=config_id,items=items,next_revision=items[-1]['revision'] if len(rows)>limit else None,
                    immutable_history=True,privileged_rewrite_protected=False,product_accepted=False)

    def begin_worker(self,p,run_id):
        self.s.authorize(p,'worker');ident(run_id)
        worker_id='worker-'+uuid.uuid4().hex
        capabilities=WorkerCapabilities(worker_id,{CAPABILITY},1.0,0.25,max_concurrency=1)
        capabilities.validate();now=time.time()
        with self.s.catalog.tx() as db:
            _,body=self.s.catalog.intent(db,p,run_id)
            require(db.execute('SELECT COUNT(*) FROM workers').fetchone()[0]<10000,'worker_history_full',429)
            self.s.catalog.reserve_worker(db,worker_id)
            worker=dict(worker_id=worker_id,run_id=run_id,native_job_id=body['native_job_id'],capabilities=[CAPABILITY],
                        state='DISPATCHING',timestamp=now,started_at=now,finished_at=None,active_tasks=1,capacity=1,
                        error_rate=0.0,declared_cpu_cores=1.0,declared_memory_gb=0.25,
                        resources_measured=False,outcome=None,evidence_origin='CONTROLLED_OPERATOR_EXECUTION')
            db.execute('INSERT INTO workers VALUES(?,?,?)',(worker_id,p.tenant,canonical(worker).decode()))
            self.s.catalog.event(db,p.actor,'WORKER_DISPATCH_STARTED',worker_id,dict(run_id=run_id),reservation=worker_id)
        return worker_id

    def finish_worker(self,p,worker_id,outcome):
        # Internal completion telemetry of a previously authorized execution.
        # No credential/worker registration endpoint exists; no exception details.
        require(outcome in ('ACKED','FAILED','IDLE','PAUSED','CANCELLED','TERMINAL','INTERRUPTED'),
                'worker_outcome_invalid');ident(worker_id)
        with self.s.catalog.tx(read_only=True) as db:
            row=db.execute('SELECT body FROM workers WHERE id=? AND tenant=?',(worker_id,p.tenant)).fetchone()
            require(row is not None,'worker_not_found',404)
            previous=json.loads(row[0])
            if previous['state']=='STOPPED' and 'reconciliation' in previous:
                # An authorized reconciliation may win the completion gap.
                # It already released credits; never append a second completion.
                return
        try:
            with self.s.catalog.tx(reservation=worker_id) as db:
                row=db.execute('SELECT body FROM workers WHERE id=? AND tenant=?',(worker_id,p.tenant)).fetchone()
                require(row is not None,'worker_not_found',404);body=json.loads(row[0])
                require(body['state']=='DISPATCHING','worker_already_finished')
                body.update(state='STOPPED',timestamp=time.time(),finished_at=time.time(),active_tasks=0,
                            error_rate=1.0 if outcome in ('FAILED','INTERRUPTED') else 0.0,outcome=outcome)
                db.execute('UPDATE workers SET body=? WHERE id=?',(canonical(body).decode(),worker_id))
                self.s.catalog.event(db,p.actor,'WORKER_DISPATCH_FINISHED',worker_id,
                                     dict(run_id=body['run_id'],outcome=outcome),reservation=worker_id,final_reservation=True)
        except OperatorError as e:
            if e.code!='audit_reservation_missing':raise
            # Reconciliation can win after the read above but before admission
            # to the reserved write transaction. Verify its durable, audit-bound
            # STOPPED record before treating the completion as already settled.
            # A missing reservation without that record remains an error.
            with self.s.catalog.tx(read_only=True) as db:
                row=db.execute('SELECT body FROM workers WHERE id=? AND tenant=?',(worker_id,p.tenant)).fetchone()
                if row is not None:
                    body=json.loads(row[0])
                    if body['state']=='STOPPED' and 'reconciliation' in body:return
            raise

    def check_dispatch(self,db,p,worker_id,run_id):
        row=db.execute('SELECT body FROM workers WHERE id=? AND tenant=?',(worker_id,p.tenant)).fetchone()
        require(row is not None,'worker_not_found',404)
        body=json.loads(row[0])
        require(body['state']=='DISPATCHING' and body['run_id']==run_id,'worker_dispatch_fenced')

    def reconcile_worker(self,p,worker_id,expected_record_sha256,key):
        """Fence an abandoned dispatch and release its own unused audit credits.

        No process is killed, no heartbeat proves death, no queue is redriven.
        A proven terminal result may finish its interrupted acknowledgement and
        idempotency/run finalization; its attempt/result is never rewritten.
        RUNNING work remains review-only. The same
        catalogue write lock fences a late dispatch before native processing.
        """
        self._auth(p,'admin_recover');ident(worker_id);ident(key)
        require(type(expected_record_sha256) is str and HASH.fullmatch(expected_record_sha256),
                'invalid_worker_recovery',400)
        fingerprint=digest(dict(worker=worker_id,before=expected_record_sha256,key=key,tenant=p.tenant))
        def read(db):
            row=db.execute('SELECT body FROM workers WHERE id=? AND tenant=?',(worker_id,p.tenant)).fetchone()
            require(row is not None,'worker_not_found',404)
            return json.loads(row[0])
        def replay(body):
            require(body['state']=='STOPPED' and 'reconciliation' in body,'worker_not_recoverable')
            r=body['reconciliation'];require(r['fingerprint']==fingerprint,'idempotency_conflict')
            return dict(r['result'],replayed=True)
        with self.s.catalog.tx(read_only=True) as db:
            body=read(db)
            if body['state']=='STOPPED':return replay(body)
        try:
            with self.s.catalog.tx(reservation=worker_id) as db:
                self._auth(p,'admin_recover');body=read(db)
                require(body['state']=='DISPATCHING','worker_not_recoverable')
                require(digest(body)==expected_record_sha256,'stale_worker_record')
                _,run=self.s.catalog.intent(db,p,body['run_id'])
                require(run['native_job_id']==body['native_job_id'],'worker_record_invalid')
                self.s._no_pending_control(db,p,body['run_id'])
                with self.s.native(run) as native:
                    from .terminal_recovery import finalize_verified_terminal
                    finalization=finalize_verified_terminal(self.s,p,native,run,worker_id)
                    _,attempt,q=self.s._snapshot(native,run)
                    require(attempt['state']!='RUNNING','worker_recovery_requires_quiescent_state')
                    # _snapshot verifies the full native transition/queue/CAS binding.
                    self._queue_item(run,q,None,time.time())
                outcome='INTERRUPTED' if attempt['state']=='READY' else 'TERMINAL'
                result=dict(worker_id=worker_id,run_id=body['run_id'],lifecycle='STOPPED',outcome=outcome,
                    engine_state=attempt['state'],queue_state=q.state,
                    scope='VERIFIED_TERMINAL_FINALIZATION' if any(finalization.values()) else 'DISPATCH_ADMISSION_ONLY',
                    process_termination_claimed=False,job_state_modified=finalization['native_run_state_modified'],
                    worker_dispatched=False,**finalization,
                    product_accepted=False)
                now=time.time()
                body.update(state='STOPPED',timestamp=now,finished_at=now,active_tasks=0,
                    error_rate=1.0 if outcome=='INTERRUPTED' else 0.0,outcome=outcome,
                    reconciliation=dict(fingerprint=fingerprint,before_sha256=expected_record_sha256,result=result))
                db.execute('UPDATE workers SET body=? WHERE id=?',(canonical(body).decode(),worker_id))
                self.s.catalog.event(db,p.actor,'WORKER_DISPATCH_RECONCILED',worker_id,
                    dict(run_id=body['run_id'],before_sha256=expected_record_sha256,outcome=outcome,
                         engine_state=attempt['state'],queue_state=q.state),
                    reservation=worker_id,final_reservation=True)
                return dict(result,replayed=False)
        except OperatorError as e:
            if e.code!='audit_reservation_missing':raise
            # A concurrent same-intent reconciliation won. Read-only replay is
            # allowed at exact quota; never borrow somebody else's credits.
            with self.s.catalog.tx(read_only=True) as db:
                self._auth(p,'admin_recover');return replay(read(db))

    def workers(self,p,after=None,limit=25):
        self._auth(p);page(after,limit);now=time.time();items=[]
        with self.s.catalog.tx(read_only=True) as db:
            rows=db.execute('SELECT id,body FROM workers WHERE tenant=? AND id>? ORDER BY id LIMIT ?',
                            (p.tenant,after or '',limit+1)).fetchall()
            for row in rows[:limit]:
                w=json.loads(row[1]);ident(w['worker_id']);number(w['timestamp']);number(w['error_rate'],maximum=1)
                require(w['timestamp']<=now+5 and w['state'] in ('DISPATCHING','STOPPED') and
                        w['capabilities']==[CAPABILITY] and w['worker_id']==row[0] and
                        w['resources_measured'] is False and w['evidence_origin']=='CONTROLLED_OPERATOR_EXECUTION',
                        'worker_record_invalid')
                number(w['started_at']);require(w['started_at']<=w['timestamp'],'worker_record_invalid')
                require(w['declared_cpu_cores']==1.0 and w['declared_memory_gb']==0.25,'worker_record_invalid')
                if w['state']=='STOPPED':
                    number(w['finished_at']);require(w['finished_at']>=w['started_at'] and w['active_tasks']==0 and
                        w['outcome'] in ('ACKED','FAILED','IDLE','PAUSED','CANCELLED','TERMINAL','INTERRUPTED'),
                        'worker_record_invalid')
                else:require(w['finished_at'] is None and w['outcome'] is None and w['active_tasks']==1,'worker_record_invalid')
                count(w['active_tasks'],1);require(type(w['capacity']) is int and w['capacity']==1,'worker_capacity_invalid')
                heartbeat=WorkerHeartbeat(w['worker_id'],w['timestamp'],w['active_tasks'],w['capacity'],w['error_rate'])
                health=worker_health(heartbeat,now)
                capabilities=WorkerCapabilities(w['worker_id'],set(w['capabilities']),w['declared_cpu_cores'],w['declared_memory_gb'],max_concurrency=w['capacity'])
                capabilities.validate()
                _,run=self.s.catalog.intent(db,p,w['run_id'])
                require(w['native_job_id']==run['native_job_id'],'worker_record_invalid')
                with self.s.native(run) as native:
                    consistency='VERIFIED'
                    try:_,attempt,q=self.s._snapshot(native,run)
                    except OperatorError as error:
                        if error.code!='native_state_inconsistent':raise
                        _,attempt,q=self.s._native_identity(native,run)
                        require(attempt['state'] in ('SUCCEEDED','FAILED') and q.state=='DELIVERED' and
                                q.consumer_id==w['worker_id'] and w['state']=='DISPATCHING',
                                'native_state_inconsistent')
                        consistency='REVIEW_REQUIRED_PARTIAL_FINALIZATION'
                    lease=self._queue_item(run,q,None,now)
                owns=q.consumer_id==w['worker_id'] and q.state=='DELIVERED'
                items.append(dict(worker_id=w['worker_id'],run_id=w['run_id'],capability_tags=w['capabilities'],
                    lifecycle=w['state'],health=health,heartbeat_at=w['timestamp'],active_tasks=w['active_tasks'],capacity=w['capacity'],
                    current_workload=[dict(run_id=w['run_id'],stage_id=STAGE_ID,task_id=q.task.task_id)] if owns else [],
                    dispatch_pending=w['state']=='DISPATCHING' and not owns,queue_state=q.state,
                    lease_status=lease['lease_status'],lease_visible_at=q.visible_at if owns else None,
                    liveness='UNVERIFIED_STALE' if health=='STALE' and w['state']!='STOPPED' else w['state'],
                    outcome=w['outcome'],resources_measured=False,heartbeat_refresh_mode='START_AND_COMPLETION_ONLY',
                    native_consistency=consistency,
                    record_sha256=digest(w),can_reconcile=('admin_recover' in p.permissions and
                        w['state']=='DISPATCHING' and attempt['state']!='RUNNING'),
                    death_inferred_from_stale=False,product_accepted=False))
        return dict(status='AVAILABLE' if items else 'NOT_RUN',items=items,next_after=items[-1]['worker_id'] if len(rows)>limit else None,
                    current_health_not_process_attestation=True,product_accepted=False)

    def _queue_item(self,body,q,control,now):
        t=q.task;t.validate()
        require(t.task_id=='inspect-'+body['native_job_id'][4:] and t.run_id==body['native_job_id'] and
                t.stage_id==STAGE_ID and t.attempt==1 and t.required_capability_tags==[CAPABILITY] and
                t.input_artifact_refs==['source-'+body['native_job_id'][4:]] and t.idempotency_key==body['native_key'] and
                t.max_deliveries==1 and t.priority==100 and q.state in VALID_STATES,'queue_identity_invalid')
        count(q.delivery_count,1000);count(t.priority);count(t.max_deliveries,1000)
        require(q.delivery_count<=t.max_deliveries,'queue_delivery_count_invalid')
        number(t.created_at);number(q.visible_at)
        for v in (q.delivered_at,q.acked_at):
            if v is not None:number(v)
        require(t.created_at<=now+5 and (q.consumer_id is None or type(q.consumer_id) is str and len(q.consumer_id)<=100),
                'queue_timing_or_consumer_invalid')
        if q.consumer_id is not None:ident(q.consumer_id)
        require((q.delivery_count==0)==(q.delivered_at is None),'queue_transition_invalid')
        if q.delivered_at is not None:
            require(t.created_at<=q.delivered_at<=now+5,'queue_transition_invalid')
        require((q.state=='ACKED')==(q.acked_at is not None),'queue_transition_invalid')
        if q.acked_at is not None:require(q.delivered_at is not None and q.delivered_at<=q.acked_at<=now+5,'queue_transition_invalid')
        if q.state=='DELIVERED':require(q.consumer_id is not None and q.delivery_count==1,'queue_transition_invalid')
        if q.state in ('READY','DEAD_LETTER'):require(q.consumer_id is None,'queue_transition_invalid')
        lease='EXPIRED_REVIEW_REQUIRED' if q.state=='DELIVERED' and q.visible_at<=now else 'ACTIVE' if q.state=='DELIVERED' else 'NONE'
        safe=dict(run_id=body['run_id'],native_job_id=t.run_id,task_id=t.task_id,stage_id=t.stage_id,attempt=t.attempt,
                  state=q.state,delivery_count=q.delivery_count,max_deliveries=t.max_deliveries,priority=t.priority,
                  created_at=t.created_at,visible_at=q.visible_at,delivered_at=q.delivered_at,acked_at=q.acked_at,
                  consumer_id=q.consumer_id,required_capability_tags=t.required_capability_tags,lease_status=lease,
                  source_hash=body['source_hash'],executor_admission=control,**safe_reason(q.last_reason))
        return dict(safe,queue_digest=digest(safe))

    def queue(self,p,after=None,limit=25,state=None):
        self._auth(p);page(after,limit)
        require(state is None or state in VALID_STATES,'invalid_queue_filter',400)
        items=[];scanned=0;last=None;now=time.time()
        with self.s.catalog.tx(read_only=True) as db:
            rows=db.execute('SELECT id FROM intents WHERE tenant=? AND id>? ORDER BY id LIMIT 257',
                            (p.tenant,after or '')).fetchall()
            for row in rows[:256]:
                catalog_row,body=self.s.catalog.intent(db,p,row[0]);last=row[0];scanned+=1
                with self.s.native(body) as native:_,attempt,q=self.s._snapshot(native,body)
                if state is None or q.state==state:
                    items.append(self._queue_item(body,q,catalog_row['control'],now))
                    if len(items)==limit:break
            more=scanned<len(rows)
        return dict(status='AVAILABLE' if items else 'EMPTY',items=items,next_after=last if more else None,
                    scanned_runs=scanned,scan_limit=256,filtered_state=state,mutating_lease_recovery_performed=False,
                    queue_scope='TENANT_OWNED_CONTROLLED_PDF_NAMESPACES',product_accepted=False)

    def dead_letter(self,p,run_id,after_sequence=0,limit=25):
        self._auth(p);ident(run_id);count(after_sequence,1000000);page(None,limit)
        with self.s.catalog.tx(read_only=True) as db:
            row,body=self.s.catalog.intent(db,p,run_id)
            with self.s.native(body) as native:
                _,attempt,q=self.s._snapshot(native,body)
                require(q.state=='DEAD_LETTER','not_dead_letter')
                connection=native.queue._connect()
                try:
                    connection.execute('PRAGMA query_only=ON')
                    total=connection.execute('SELECT COUNT(*) FROM queue_events WHERE task_id=?',(q.task.task_id,)).fetchone()[0]
                finally:connection.close()
                require(total<=1000,'queue_event_inventory_limit')
                events=native.queue.events(q.task.task_id)
            safe=[];previous=0
            for e in events:
                count(e['sequence'],1000000);number(e['event_at']);count(e['delivery_count'],1000)
                require(e['sequence']>previous and e['event_type'] in EVENTS,'queue_event_invalid');previous=e['sequence']
                if e['sequence']>after_sequence:
                    safe.append(dict(sequence=e['sequence'],event_type=e['event_type'],event_at=e['event_at'],
                                     delivery_count=e['delivery_count'],**safe_reason(e['reason'])))
            queue=self._queue_item(body,q,row['control'],time.time())
        recoverable=attempt['state']=='FAILED' and row['control']!='CANCELLED'
        return dict(queue=queue,engine_state=attempt['state'],events=safe[:limit],
                    next_sequence=safe[limit-1]['sequence'] if len(safe)>limit else None,
                    recovery_action='CREATE_GOVERNED_CHILD_RETRY' if recoverable else 'REVIEW_REQUIRED',
                    can_recover=recoverable and {'admin_recover','read','retry','create'}<=p.permissions,
                    parent_revision=row['revision'],failed_parent_will_be_preserved=True,
                    native_redrive_not_safe_for_terminal_pdf_run=True,product_accepted=False)

    def recover_dead_letter(self,p,run_id,key,expected_revision,expected_queue_digest):
        self._auth(p,'admin_recover');ident(key)
        require(type(expected_revision) is int and expected_revision>=1 and type(expected_queue_digest) is str and
                HASH.fullmatch(expected_queue_digest),'invalid_recovery_request',400)
        detail=self.dead_letter(p,run_id)
        require(detail['can_recover'],'dead_letter_recovery_unavailable')
        require(detail['parent_revision']==expected_revision and detail['queue']['queue_digest']==expected_queue_digest,
                'stale_dead_letter_state')
        # Canonical service retry preserves terminal parent and source/config
        # lineage. It also rechecks FAILED status and durable idempotency.
        child=self.s.retry(p,run_id,key,expected_revision=expected_revision,expected_queue_digest=expected_queue_digest)
        with self.s.catalog.tx() as db:
            row,parent=self.s.catalog.intent(db,p,run_id);_,new=self.s.catalog.intent(db,p,child['run_id'])
            require(row['revision']==expected_revision and new['parent_run_id']==run_id and
                    new['source_hash']==parent['source_hash'] and new['source_id']==parent['source_id'],
                    'retry_lineage_invalid')
            # One recovery audit receipt per governed child, including replay.
            found=any(json.loads(r[0])['action']=='DEAD_LETTER_CHILD_CREATED' and json.loads(r[0])['target']==child['run_id']
                      for r in db.execute('SELECT body FROM audit ORDER BY n'))
            if not found:self.s.catalog.event(db,p.actor,'DEAD_LETTER_CHILD_CREATED',child['run_id'],
                                              dict(parent_run_id=run_id,queue_digest=expected_queue_digest))
        current=self.s.status(p,child['run_id'])
        return dict(child,child_status=current['status'],child_queue_state=current['queue_state'],
                    parent_run_id=run_id,recovery_mode='GOVERNED_CHILD_RETRY',parent_state='FAILED',
                    original_queue_state='DEAD_LETTER',worker_dispatched=False)
