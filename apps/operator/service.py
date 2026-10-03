"""Real operator journeys delegated to canonical PDF, persistence, CAS and queue.

One private canonical PDF-service namespace per operator run permits truthful
queued admission controls without changing the pre-existing Android/API worker.
Only the controlled operator worker may consume these namespaces. Do not point
the old unguarded worker at one. No running-process interruption is claimed.
"""
from contextlib import contextmanager
from pathlib import Path
import hashlib, json, os, stat, tempfile, time

from apps.api.job_service import PdfInspectionJobService, STAGE_ID
from bie.document_intelligence.real_pdf_runtime import inspect_real_pdf, RealPdfRuntimeError
from bie.infrastructure.artifact_store import FileSystemCAS, BlobRef
from bie.infrastructure.persistence import PersistedArtifactRecord, PersistedAttempt, PersistedEvent
from bie.infrastructure.run_api import RunAPI, CreateRunRequest, RunView
from bie.infrastructure.run_config import RunConfig
from .catalog import Catalog, timestamp
from .resources import OwnedPersistence
from .contracts import (OperatorError, require, ident, digest, canonical, private_path,
                        run_options, MAX_PDF_BYTES, HASH)
from .pdf_validation import inspect_source

SAFE_REASONS = {'source_stored','worker_started','inspection_complete','pdf_inspection_failed',
                'internal_worker_error','operator_cancelled','cas_capacity_reached','cas_blob_too_large'}

class Service:
    def __init__(self, root, credentials, max_pdf_bytes=MAX_PDF_BYTES,cas_limits=None):
        self.root = private_path(root)
        self.root.mkdir(parents=True,exist_ok=True)
        self.credentials = credentials
        require(type(max_pdf_bytes) is int and 0 < max_pdf_bytes <= MAX_PDF_BYTES, 'invalid_size_configuration')
        self.limit = max_pdf_bytes
        self.catalog = Catalog(self.root)
        from .cas_budget import CASBudget,BudgetedCAS
        self.cas_budget=CASBudget(self.root,cas_limits)
        self.catalog.storage_policy_sha256=self.cas_budget.policy_sha256
        with self.catalog.tx(read_only=True):pass
        self.cas = BudgetedCAS(private_path(self.root,'sources-cas'),self.cas_budget)
        private_path(self.root,'staging').mkdir(exist_ok=True)
        private_path(self.root,'runs').mkdir(exist_ok=True)
        from .administration import Administration
        self.administration=Administration(self)
        from .governance import Governance
        self.governance=Governance(self)
        from .admission import for_root
        self._creation_admission=for_root(self.root)

    def authorize(self,p,permission): self.credentials.check(p,permission)

    def staging(self):
        return tempfile.NamedTemporaryFile(mode='w+b',prefix='upload-',dir=private_path(self.root,'staging'),delete=True)

    def import_pdf(self,p,data):
        """Bounded bytes after streaming staging. Never return PDF metadata strings."""
        self.authorize(p,'source')
        require(type(data) is bytes and 0 < len(data) <= self.limit,'invalid_source_size',400)
        sha = hashlib.sha256(data).hexdigest()
        source_id = 'src-'+digest(dict(tenant=p.tenant,sha256=sha))
        with self.catalog.tx() as db:
            existing = db.execute('SELECT body FROM sources WHERE id=? AND tenant=?',(source_id,p.tenant)).fetchone()
            if existing: return dict(json.loads(existing[0]),duplicate=True)
            require(db.execute('SELECT COUNT(*) FROM sources').fetchone()[0] < 10000,'source_catalog_full',429)
            validation = inspect_source(data)
            blob = self.cas.put_bytes(data) if validation['status']=='VALID' else None
            body = dict(source_id=source_id,sha256=sha,size_bytes=len(data),media_type='application/pdf',
                        validation=validation,stored=blob is not None,source_privacy='PRIVATE_LOCAL_CAS',
                        byte_length=len(data),fixture_acceptance=False)
            db.execute('INSERT INTO sources VALUES(?,?,?)',(source_id,p.tenant,canonical(body).decode()))
            self.catalog.event(db,p.actor,'SOURCE_VALIDATED',source_id,dict(status=validation['status']))
        return dict(body,duplicate=False)

    def source(self,p,source_id):
        self.authorize(p,'read'); ident(source_id)
        with self.catalog.tx(read_only=True) as db: return self.catalog.source(db,p,source_id)

    def _raw_source(self,source):
        private_path(self.root,'sources-cas','blobs','sha256',source['sha256'][:2],source['sha256'])
        return self.cas.get_bytes(BlobRef('sha256',source['sha256'],source['byte_length']))

    @contextmanager
    def native(self,body):
        root = private_path(self.root,'runs',ident(body['run_id']))
        # Bound the read-side preflight too: non-CAS entries must not bypass
        # the existing inventory ceilings via an unbounded rglob traversal.
        self._verify_native_tree(root)
        svc = PdfInspectionJobService(root)
        from .cas_budget import BudgetedCAS
        svc.cas = BudgetedCAS(root/'cas',self.cas_budget)
        svc.persistence = OwnedPersistence(root/'runs.sqlite3')
        try: yield svc
        finally: svc.close()

    def _verify_native_tree(self,root):
        entries=0
        def visit(directory,depth=0):
            nonlocal entries
            require(depth<=16,'native_inventory_depth_reached',503)
            private_path(self.root,directory.relative_to(self.root))
            with os.scandir(directory) as children:
                for item in children:
                    entries+=1
                    require(entries<=self.cas_budget.limits.max_inventory_entries,
                            'native_inventory_capacity_reached',503)
                    require(not item.is_symlink(),'storage_link_rejected')
                    try:info=os.stat(item.path,follow_symlinks=False)
                    except FileNotFoundError:
                        # A volatile SQLite sidecar can vanish on last close.
                        # Native stores still verify their own opened records.
                        require(item.name in ('runs.sqlite3-wal','runs.sqlite3-shm',
                            'queue.sqlite3-wal','queue.sqlite3-shm',
                            'idempotency.sqlite3-wal','idempotency.sqlite3-shm'),
                            'native_inventory_changed',503)
                        continue
                    if stat.S_ISDIR(info.st_mode):visit(Path(item.path),depth+1)
                    else:require(stat.S_ISREG(info.st_mode) and info.st_nlink==1,'storage_link_rejected')
        try:
            if root.exists():visit(root)
        except OSError:
            raise OperatorError('native_inventory_unavailable',503) from None

    def create(self,p,source_id,options,key,parent=None,expected_parent_revision=None,expected_parent_queue_digest=None,policy_binding=None):
        self.authorize(p,'create');ident(source_id);ident(key)
        normalized=run_options(options)
        if policy_binding is not None:
            from .governance import shape,integer,hash_value
            shape(policy_binding,('config_id','revision','configuration_sha256'))
            ident(policy_binding['config_id']);integer(policy_binding['revision'],1);hash_value(policy_binding['configuration_sha256'])
            policy_binding=dict(policy_binding)
        # Exact intent and parent preconditions only. Conflicting requests never
        # share a success; canonical persisted idempotency remains authoritative.
        admission_key=digest(dict(tenant=p.tenant,source=source_id,config=normalized,key=key,parent=parent,
            parent_revision=expected_parent_revision,parent_queue=expected_parent_queue_digest,policy_binding=policy_binding))
        result,coalesced=self._creation_admission.run(admission_key,lambda:self._create(p,source_id,normalized,key,
            parent,expected_parent_revision,expected_parent_queue_digest,policy_binding))
        # A waiting caller may have expired or been revoked during native I/O.
        self.authorize(p,'create')
        return dict(result,replayed=True) if coalesced else result

    def _create(self,p,source_id,options,key,parent=None,expected_parent_revision=None,expected_parent_queue_digest=None,policy_binding=None):
        self.authorize(p,'create'); ident(source_id); ident(key)
        normalized = run_options(options)
        key_hash = digest(dict(tenant=p.tenant,key=key))
        identity=dict(source=source_id,config=normalized,parent=parent)
        if policy_binding is not None:identity['policy_binding']=policy_binding
        fingerprint = digest(identity)
        run_id = 'run-'+digest(dict(tenant=p.tenant,key=key_hash,fingerprint=fingerprint))
        with self.catalog.tx() as db:
            if parent:
                parent_row,parent_body=self.catalog.intent(db,p,ident(parent))
                with self.native(parent_body) as parent_native:
                    _,parent_attempt,parent_queue=self._snapshot(parent_native,parent_body)
                require(parent_attempt['state']=='FAILED' and parent_queue.state=='DEAD_LETTER',
                        'retry_requires_failed_parent')
                if expected_parent_revision is not None:
                    require(parent_row['revision']==expected_parent_revision and
                            self.administration._queue_item(parent_body,parent_queue,parent_row['control'],
                                time.time())['queue_digest']==expected_parent_queue_digest,'stale_dead_letter_state')
            old = db.execute('SELECT * FROM intents WHERE tenant=? AND key_hash=?',(p.tenant,key_hash)).fetchone()
            if old:
                require(old['fingerprint']==fingerprint, 'idempotency_conflict')
            source = self.catalog.source(db,p,source_id)
            require(source['validation']['status']=='VALID' and source['stored'],'source_not_valid')
            metadata=[('engine_profile',normalized['profile'])]
            if policy_binding is not None:
                if old:
                    # Exact existing intent may replay after policy deactivation;
                    # its canonical config is never rebuilt from a newer version.
                    version=self.governance._version(db,p,'policy',policy_binding['config_id'],policy_binding['revision'])
                    require(version['configuration_sha256']==policy_binding['configuration_sha256'],'configuration_pin_mismatch')
                else:
                    version=self.governance.binding(db,p,policy_binding['config_id'],policy_binding['revision'],policy_binding['configuration_sha256'])
                effective=version['configuration']
                require(normalized['locale']==effective['locale'] and normalized['model_policy']==effective['model_policy'],
                        'policy_options_conflict')
                require(source['size_bytes']<=effective['limits']['pdf_bytes'],'policy_source_too_large',413)
                metadata.extend([('policy_id',version['config_id']),('policy_revision',str(version['revision'])),
                    ('policy_sha256',version['configuration_sha256'])])
            cfg=RunConfig(1,run_id,source_id,tuple(normalized['outputs']),normalized['model_policy'],
                          normalized['locale'],True,tuple(metadata))
            config=cfg.to_canonical_dict();config_hash=digest(config)
            require(db.execute('SELECT COUNT(*) FROM intents').fetchone()[0] < 10000 or old is not None,
                    'run_catalog_full',429)
            native_key = 'op-'+digest(dict(run_id=run_id))
            body = dict(run_id=run_id,source_id=source_id,source_hash=source['sha256'],config_hash=config_hash,
                        config=config,parent_run_id=parent,engine_profile=normalized['profile'],native_key=native_key)
            # Canonical RunAPI is really executed; adapter delegates native creation.
            service = self
            class Store:
                def create(self,request):
                    require(request.source_ref==source_id and request.config_hash==config_hash,'canonical_request_mismatch')
                    with service.native(body) as native:
                        submission = native.submit(service._raw_source(source),native_key)
                        body['native_job_id'] = submission['job_id']
                        service._register(native,body,'operator.run.config',canonical(config),
                                          {'config_hash':config_hash})
                        if parent:
                            service._register(native,body,'operator.run.lineage',canonical(dict(parent_run_id=parent,
                                child_run_id=run_id,source_hash=source['sha256'],config_hash=config_hash)),
                                {'parent_run_id':parent})
                    return RunView(run_id,submission['status'],source_id,config_hash)
            view = RunAPI(Store()).create(CreateRunRequest(source_id,config_hash))
            if not old:
                db.execute('INSERT INTO intents VALUES(?,?,?,?,?,?,?)',
                           (run_id,p.tenant,key_hash,fingerprint,canonical(body).decode(),'READY',1))
                self.catalog.event(db,p.actor,'RUN_CREATED',run_id,dict(parent_run_id=parent,config_hash=config_hash))
            else:
                require(json.loads(old['body'])==body,'intent_identity_mismatch')
        return dict(run_id=view.run_id,engine_profile=normalized['profile'],replayed=old is not None,
                    config_hash=config_hash,source_hash=source['sha256'],product_accepted=False)

    def _register(self,native,body,kind,raw,metadata,evidence=False):
        blob = native.cas.put_bytes(raw)
        artifact = 'opart-'+digest(dict(run=body['run_id'],kind=kind,blob=blob.digest))
        source_id = 'source-'+body['native_job_id'][4:]
        native.persistence.register_artifact(PersistedArtifactRecord(artifact,kind,blob.algorithm,blob.digest,
            blob.size,body['native_job_id'],STAGE_ID,evidence,metadata,[source_id]))
        return artifact,blob.digest

    def _snapshot(self,native,body):
        snap,attempt,queue=self._native_identity(native,body)
        consistent = {'READY':{'READY'},'RUNNING':{'DELIVERED','DEAD_LETTER'},
                      'SUCCEEDED':{'ACKED'},'FAILED':{'DEAD_LETTER'},'BLOCKED':{'DEAD_LETTER'}}
        require(attempt['state'] in consistent and queue.state in consistent[attempt['state']],
                'native_state_inconsistent')
        return snap,attempt,queue

    def _native_identity(self,native,body):
        # Shared immutable identity/history checks only. Ordinary reads still
        # require _snapshot's strict queue/attempt consistency. Only the explicit
        # authorized terminal reconciler can inspect a partially finalized queue.
        snap = native.persistence.load_run_state(body['native_job_id'])
        stages = snap['stages']
        require(set(stages)=={STAGE_ID},'native_stage_inventory_changed')
        attempts = stages[STAGE_ID]['attempts']
        require(len(attempts)==1,'native_attempt_inventory_changed')
        attempt = attempts[0]
        queue = native.queue.get('inspect-'+body['native_job_id'][4:])
        state = attempt['state']
        prior='PENDING'
        for event in snap['events']:
            require(event['stage_id']==STAGE_ID and event['attempt']==1 and event['from_state']==prior,
                    'native_transition_history_inconsistent')
            prior=event['to_state']
        require(prior==state,'native_transition_history_inconsistent')
        source = native.persistence.load_artifact('source-'+body['native_job_id'][4:])
        require(source.blob_digest==body['source_hash'] and source.run_id==body['native_job_id'], 'native_source_tampered')
        # Config integrity is re-read from canonical CAS, not just the mutable index.
        _,config_sha = self._config_ref(native,body)
        require(config_sha==body['config_hash'],'native_config_tampered')
        return snap,attempt,queue

    def _config_ref(self,native,body):
        matches = []
        for aid in native.persistence.artifacts_for_run(body['native_job_id']):
            rec = native.persistence.load_artifact(aid)
            if rec.artifact_type=='operator.run.config':
                raw = native.cas.get_bytes(BlobRef(rec.blob_algorithm,rec.blob_digest,rec.blob_size))
                require(json.loads(raw)==body['config'],'native_config_tampered')
                matches.append((aid,hashlib.sha256(raw).hexdigest()))
        require(len(matches)==1,'native_config_inventory_changed')
        return matches[0]

    def status(self,p,run_id):
        self.authorize(p,'read'); ident(run_id)
        with self.catalog.tx(read_only=True) as db:
            row,body = self.catalog.intent(db,p,run_id)
            self._no_pending_control(db,p,run_id)
            with self.native(body) as native:
                snap,attempt,queue = self._snapshot(native,body)
                engine_state = attempt['state']
                control = row['control']
                require(control!='CANCELLED' or (engine_state=='BLOCKED' and
                    any(e['reason']=='operator_cancelled' for e in snap['events'])), 'cancel_receipt_missing')
                require(control!='PAUSED' or engine_state=='READY','paused_native_state_changed')
                status = control if control in ('PAUSED','CANCELLED') else engine_state
                if engine_state=='RUNNING' and queue.state=='DEAD_LETTER': status='REVIEW_REQUIRED'
                outputs = []
                if engine_state=='SUCCEEDED':
                    result = native.result(body['native_job_id'])
                    require(result['source_hash']==body['source_hash'],'result_source_mismatch')
                    outputs = list(attempt['output_artifact_refs'])
            return dict(run_id=run_id,native_job_id=body['native_job_id'],status=status,
                engine_state=engine_state,engine_run_state=snap['run_state'],queue_state=queue.state,
                executor_admission=control,revision=row['revision'],source_id=body['source_id'],
                source_hash=body['source_hash'],config_hash=body['config_hash'],parent_run_id=body['parent_run_id'],
                result_available=engine_state=='SUCCEEDED',artifact_refs=outputs,
                learning_outputs={o:{'status':'NOT_RUN','reason':'learning_producer_not_bound'}
                                  for o in body['config']['enabled_outputs']},
                inspection_only=True,product_accepted=False)

    def list_runs(self,p,offset=0,limit=25):
        self.authorize(p,'read')
        require(type(offset) is int and 0<=offset<=10000 and type(limit) is int and 1<=limit<=100,'invalid_pagination',400)
        with self.catalog.tx(read_only=True) as db:
            ids = [r[0] for r in db.execute('SELECT id FROM intents WHERE tenant=? ORDER BY id LIMIT ? OFFSET ?',
                                           (p.tenant,limit+1,offset))]
        return dict(items=[self.status(p,r) for r in ids[:limit]],next_offset=offset+limit if len(ids)>limit else None)

    def timeline(self,p,run_id,after=0,limit=100):
        self.authorize(p,'read'); ident(run_id)
        require(type(after) is int and after>=0 and type(limit) is int and 1<=limit<=100,'invalid_pagination',400)
        with self.catalog.tx(read_only=True) as db:
            _,body = self.catalog.intent(db,p,run_id)
            with self.native(body) as native:
                snap,_,_ = self._snapshot(native,body)
            events = [dict(e,event_origin='CANONICAL_PERSISTENCE',
                           reason=e['reason'] if e['reason'] in SAFE_REASONS else 'diagnostic_redacted') for e in snap['events']]
            for r in db.execute('SELECT n,body,sha FROM audit ORDER BY n'):
                b = json.loads(r['body'])
                if b['target']==run_id:
                    events.append(dict(sequence=r['n'],stage_id='OPERATOR_ADMISSION',from_state=None,
                        to_state=b['action'],attempt=1,timestamp=b['timestamp'],reason=b['action'],
                        evidence_refs=[],event_origin='OPERATOR_AUDIT',receipt_sha256=r['sha']))
        events.sort(key=lambda e:(e['timestamp'],e['event_origin'],e['sequence']))
        for n,e in enumerate(events,1): e['timeline_order']=n
        selected = [e for e in events if e['timeline_order']>after]
        return dict(run_id=run_id,items=selected[:limit],next_after=selected[limit-1]['timeline_order'] if len(selected)>limit else None)

    def failure(self,p,run_id):
        state = self.status(p,run_id)
        require(state['status'] in ('FAILED','BLOCKED','CANCELLED'),'failure_not_available')
        with self.catalog.tx(read_only=True) as db:
            _,body = self.catalog.intent(db,p,run_id)
            with self.native(body) as native:
                _,a,_ = self._snapshot(native,body)
                codes = [c if c in SAFE_REASONS else 'diagnostic_redacted' for c in a['diagnostics']]
        return dict(run_id=run_id,status=state['status'],diagnostic_codes=codes,evidence_refs=a['evidence_refs'],
                    message='Inspection or executor admission did not complete.',traceback_exposed=False)

    def evidence(self,p,run_id,evidence_id):
        from bie.infrastructure.evidence_api import EvidenceAPI
        self.authorize(p,'read');ident(run_id);ident(evidence_id)
        with self.catalog.tx(read_only=True) as db:
            _,body=self.catalog.intent(db,p,run_id)
            with self.native(body) as native:
                require(evidence_id in native.persistence.evidence_for_run(body['native_job_id']), 'evidence_not_found',404)
                class Store:
                    def get(self,key):
                        rec=native.persistence.load_artifact(key)
                        require(rec.run_id==body['native_job_id'] and rec.evidence and rec.blob_size<=64*1024,
                                'evidence_binding_invalid')
                        raw=native.cas.get_bytes(BlobRef(rec.blob_algorithm,rec.blob_digest,rec.blob_size))
                        document=json.loads(raw)
                        allowed={'job_id','source_hash','status','diagnostic_code','result_blob_hash',
                                 'result_byte_length','runtime_policy','page_count','total_blocks'}
                        if rec.artifact_type=='document.inspection.evidence':
                            require(type(document) is dict and set(document)<=allowed,'evidence_schema_invalid')
                            require(document.get('source_hash')==body['source_hash'],'evidence_source_mismatch')
                            if 'diagnostic_code' in document:
                                document['diagnostic_code']=document['diagnostic_code'] if document['diagnostic_code'] in SAFE_REASONS else 'diagnostic_redacted'
                        else: document={'status':'METADATA_ONLY','raw_evidence_not_exposed':True}
                        return dict(evidence_id=key,sha256=rec.blob_digest,size_bytes=rec.blob_size,
                            artifact_type=rec.artifact_type,parent_refs=rec.parent_artifact_ids,
                            provenance='CANONICAL_PERSISTED_ARTIFACT',evidence=document,product_accepted=False)
                return EvidenceAPI(Store()).get(evidence_id)

    def control(self,p,run_id,action,expected_revision):
        self.authorize(p,'control'); ident(run_id)
        require(action in ('pause','resume','cancel'),'unsupported_control',400)
        require(type(expected_revision) is int and expected_revision>=1,'revision_required',400)
        if action=='cancel':
            key='control-cancel-'+digest(dict(tenant=p.tenant,run_id=run_id,revision=expected_revision))
            result,coalesced=self._creation_admission.run(key,lambda:self._cancel(p,run_id,expected_revision))
            # A waiter never inherits the owner's authorization after revocation.
            self.authorize(p,'control')
            if coalesced:result['replayed']=True
            return result
        with self.catalog.tx() as db:
            row,body = self.catalog.intent(db,p,run_id)
            self._no_pending_control(db,p,run_id)
            require(row['revision']==expected_revision,'stale_revision')
            with self.native(body) as native:
                snap,a,q = self._snapshot(native,body)
                if row['control']=='CANCELLED':
                    require(action=='cancel','terminal_control')
                    return dict(run_id=run_id,status='CANCELLED',revision=row['revision'],replayed=True)
                require(a['state']=='READY' and q.state=='READY','running_or_terminal_control_unavailable')
                target = {'pause':'PAUSED','resume':'READY','cancel':'CANCELLED'}[action]
                if target==row['control']: return dict(run_id=run_id,status=target,revision=row['revision'],replayed=True)
                require(action!='resume' or row['control']=='PAUSED','run_not_paused')
            db.execute('UPDATE intents SET control=?,revision=revision+1 WHERE id=?',(target,run_id))
            self.catalog.event(db,p.actor,'RUN_'+target,run_id)
        return dict(run_id=run_id,status=target,revision=expected_revision+1,replayed=False,
                    control_scope='QUEUED_OPERATOR_EXECUTOR_ONLY')

    def _no_pending_control(self,db,p,run_id):
        rows=db.execute('SELECT body FROM control_operations WHERE tenant=?',(p.tenant,))
        require(not any(json.loads(row[0]).get('run_id')==run_id and
                        json.loads(row[0]).get('state')=='PENDING' for row in rows),
                'control_reconciliation_required')

    def _cancel(self,p,run_id,expected_revision):
        """Durable intent before canonical queue kill, replay exact partial steps.

        This is not a cross-database atomic transaction. Pending state prevents
        controlled dispatch; reads never claim cancelled before native proof.
        Only an authorized identical cancel can reconcile; no automatic retry.
        """
        operation='cancel-'+digest(dict(tenant=p.tenant,run_id=run_id,revision=expected_revision))
        with self.catalog.tx() as db:
            self.authorize(p,'control')
            row,body=self.catalog.intent(db,p,run_id)
            existing=db.execute('SELECT body FROM control_operations WHERE id=? AND tenant=?',
                                (operation,p.tenant)).fetchone()
            if row['control']=='CANCELLED':
                require(row['revision'] in (expected_revision,expected_revision+1),'stale_revision')
                with self.native(body) as native:
                    snap,a,q=self._snapshot(native,body)
                    require(a['state']=='BLOCKED' and any(e['reason']=='operator_cancelled' for e in snap['events']),
                            'cancel_receipt_missing')
                return dict(run_id=run_id,status='CANCELLED',revision=row['revision'],replayed=True)
            require(row['revision']==expected_revision,'stale_revision')
            if not existing:
                self._no_pending_control(db,p,run_id)
                with self.native(body) as native:
                    _,a,q=self._snapshot(native,body)
                    require(a['state']=='READY' and q.state=='READY','running_or_terminal_control_unavailable')
                self.catalog.reserve_worker(db,operation)
                document=dict(run_id=run_id,revision=expected_revision,source_hash=body['source_hash'],
                              native_job_id=body['native_job_id'],state='PENDING',action='cancel',
                              prepared_at=timestamp(),completed_at=None)
                db.execute('INSERT INTO control_operations VALUES(?,?,?)',
                           (operation,p.tenant,canonical(document).decode()))
                self.catalog.event(db,p.actor,'CANCEL_INTENT_PREPARED',run_id,
                                   dict(operation_id=operation),reservation=operation)
        try:
            return self._complete_cancel(p,run_id,expected_revision,operation,existing is not None)
        except OperatorError as exc:
            if exc.code!='audit_reservation_missing':raise
            # Another process may finish the same durable intent between the
            # prepare and complete transactions. Replay only exact committed
            # catalogue + native cancellation proof, never recreate credits.
            with self.catalog.tx(read_only=True) as db:
                self.authorize(p,'control')
                row,body=self.catalog.intent(db,p,run_id)
                saved=db.execute('SELECT body FROM control_operations WHERE id=? AND tenant=?',
                                 (operation,p.tenant)).fetchone()
                require(saved is not None,'cancel_intent_missing')
                document=json.loads(saved[0])
                require(row['control']=='CANCELLED' and row['revision']==expected_revision+1 and
                        document['state']=='COMPLETED' and document['action']=='cancel' and
                        document['revision']==expected_revision and document['run_id']==run_id and
                        document['source_hash']==body['source_hash'] and
                        document['native_job_id']==body['native_job_id'],'cancel_receipt_missing')
                with self.native(body) as native:
                    snap,a,q=self._snapshot(native,body)
                    require(snap['run_state']==a['state']=='BLOCKED' and q.state=='DEAD_LETTER' and
                            q.last_reason=='operator_cancelled' and
                            sum(e['reason']=='operator_cancelled' for e in snap['events'])==1,
                            'cancel_receipt_missing')
                return dict(run_id=run_id,status='CANCELLED',revision=row['revision'],replayed=True)

    def _complete_cancel(self,p,run_id,expected_revision,operation,replayed):
        with self.catalog.tx(reservation=operation) as db:
            self.authorize(p,'control')
            row,body=self.catalog.intent(db,p,run_id)
            saved=db.execute('SELECT body FROM control_operations WHERE id=? AND tenant=?',
                             (operation,p.tenant)).fetchone()
            require(saved is not None,'cancel_intent_missing')
            document=json.loads(saved[0])
            require(document['state']=='PENDING' and document['action']=='cancel' and
                    document['run_id']==run_id and document['revision']==row['revision']==expected_revision and
                    document['source_hash']==body['source_hash'] and document['native_job_id']==body['native_job_id'],
                    'cancel_intent_binding_invalid')
            with self.native(body) as native:
                self._finish_cancel_native(native,body)
                snap,a,q=self._snapshot(native,body)
                require(a['state']=='BLOCKED' and snap['run_state']=='BLOCKED' and q.state=='DEAD_LETTER',
                        'cancel_receipt_missing')
            document.update(state='COMPLETED',completed_at=timestamp())
            db.execute('UPDATE control_operations SET body=? WHERE id=?',
                       (canonical(document).decode(),operation))
            db.execute("UPDATE intents SET control='CANCELLED',revision=revision+1 WHERE id=?",(run_id,))
            self.catalog.event(db,p.actor,'RUN_CANCELLED',run_id,dict(operation_id=operation),
                               reservation=operation,final_reservation=True)
        return dict(run_id=run_id,status='CANCELLED',revision=expected_revision+1,replayed=replayed,
                    control_scope='QUEUED_OPERATOR_EXECUTOR_ONLY')

    def _finish_cancel_native(self,native,body):
        snap=native.persistence.load_run_state(body['native_job_id'])
        require(set(snap['stages'])=={STAGE_ID},'cancel_native_inventory_invalid')
        attempts=snap['stages'][STAGE_ID]['attempts']
        require(len(attempts)==1,'cancel_native_inventory_invalid')
        a=attempts[0];source_ref='source-'+body['native_job_id'][4:]
        q=native.queue.get('inspect-'+body['native_job_id'][4:])
        require(a['state'] in ('READY','BLOCKED') and a['input_artifact_refs']==[source_ref] and
                a['output_artifact_refs']==[] and a['evidence_refs']==[], 'cancel_native_state_invalid')
        self.administration._queue_item(body,q,None,time.time())
        require(q.state in ('READY','DEAD_LETTER') and q.delivery_count==0 and q.consumer_id is None and
                (q.state!='DEAD_LETTER' or q.last_reason=='operator_cancelled'), 'cancel_queue_state_invalid')
        source=native.persistence.load_artifact(source_ref)
        require(source.blob_digest==body['source_hash'] and source.run_id==body['native_job_id'],
                'native_source_tampered')
        _,sha=self._config_ref(native,body);require(sha==body['config_hash'],'native_config_tampered')
        previous='PENDING';cancelled=False
        for e in snap['events']:
            require(e['stage_id']==STAGE_ID and e['attempt']==1 and e['from_state']==previous and
                    e['to_state'] in ('READY','BLOCKED'),'cancel_transition_invalid')
            if e['to_state']=='BLOCKED':
                require(previous=='READY' and e['reason']=='operator_cancelled' and not cancelled,
                        'cancel_transition_invalid');cancelled=True
            previous=e['to_state']
        require(previous in ('READY','BLOCKED') and (not cancelled or a['state']=='BLOCKED') and
                (a['state']!='BLOCKED' or a['diagnostics']==['operator_cancelled']), 'cancel_transition_invalid')
        if q.state=='READY':native.queue.dead_letter(q.task.task_id,'operator_cancelled')
        if a['state']=='READY':
            native.persistence.save_attempt(body['native_job_id'],PersistedAttempt(STAGE_ID,1,'BLOCKED',
                input_artifact_refs=[source_ref],diagnostics=['operator_cancelled']))
        if not cancelled:
            native.persistence.append_event(body['native_job_id'],PersistedEvent(0,STAGE_ID,'READY','BLOCKED',1,
                timestamp(),'operator_cancelled',[]))
        native.persistence.set_run_state(body['native_job_id'],'BLOCKED')

    def work_once(self,p,run_id):
        worker_id=self.administration.begin_worker(p,run_id)
        outcome='INTERRUPTED'
        try:
            result=self._execute_once(p,run_id,worker_id)
            outcome=result['outcome']
            return result
        finally:
            self.administration.finish_worker(p,worker_id,outcome)

    def _execute_once(self,p,run_id,worker_id):
        self.authorize(p,'worker'); ident(run_id)
        with self.catalog.tx(read_only=True) as db:
            self.administration.check_dispatch(db,p,worker_id,run_id)
        # This local transaction serializes dispatch/control; no distributed guarantee.
        with self.catalog.tx(reservation=worker_id) as db:
            self.authorize(p,'worker')
            self.administration.check_dispatch(db,p,worker_id,run_id)
            row,body = self.catalog.intent(db,p,run_id)
            self._no_pending_control(db,p,run_id)
            if row['control']=='PAUSED': return {'outcome':'PAUSED','dispatched':False}
            if row['control']=='CANCELLED': return {'outcome':'CANCELLED','dispatched':False}
            with self.native(body) as native:
                _,attempt,_ = self._snapshot(native,body)
                require(attempt['state']!='RUNNING','interrupted_worker_review_required')
                if attempt['state']!='READY': return {'outcome':'TERMINAL','dispatched':False}
                try:
                    result = native.run_once(worker_id).to_safe_dict()
                except OperatorError as e:
                    if e.code not in ('cas_capacity_reached','cas_blob_too_large'):raise
                    # The native failure writer also needs CAS capacity. Only
                    # settle our proven RUNNING delivery; do not manufacture an
                    # evidence artifact or rewrite an inconsistent transition.
                    _,failed_attempt,q=self._snapshot(native,body)
                    require(failed_attempt['state']=='RUNNING' and q.state=='DELIVERED' and
                            q.consumer_id==worker_id,'quota_failure_review_required')
                    source_id='source-'+body['native_job_id'][4:]
                    native._transition(body['native_job_id'],'RUNNING','FAILED',input_refs=[source_id],
                        diagnostics=[e.code],reason=e.code)
                    native.persistence.set_run_state(body['native_job_id'],'BLOCKED')
                    native.queue.dead_letter(q.task.task_id,e.code)
                    result=dict(outcome='FAILED',job_id=body['native_job_id'],task_id=q.task.task_id)
            self.catalog.event(db,p.actor,'WORKER_FINISHED',run_id,dict(outcome=result['outcome']),reservation=worker_id)
        return dict(result,dispatched=True)

    def retry(self,p,run_id,key,*,expected_revision=None,expected_queue_digest=None):
        self.authorize(p,'retry'); ident(run_id); ident(key)
        state = self.status(p,run_id)
        require(state['status']=='FAILED','retry_requires_failed_parent')
        with self.catalog.tx(read_only=True) as db:
            _,body = self.catalog.intent(db,p,run_id)
        c = body['config']
        metadata=c['metadata'];binding=None
        if 'policy_id' in metadata:
            binding=dict(config_id=metadata['policy_id'],revision=int(metadata['policy_revision']),
                         configuration_sha256=metadata['policy_sha256'])
        return self.create(p,body['source_id'],dict(outputs=c['enabled_outputs'],locale=c['locale'],
            model_policy=c['model_policy'],profile=body['engine_profile']),'retry-'+digest(dict(parent=run_id,key=key)),
            parent=run_id,expected_parent_revision=expected_revision,expected_parent_queue_digest=expected_queue_digest,policy_binding=binding)

    def result(self,p,run_id):
        state = self.status(p,run_id)
        require(state['result_available'],'result_not_available')
        with self.catalog.tx(read_only=True) as db:
            _,body = self.catalog.intent(db,p,run_id)
            with self.native(body) as native: return native.result(body['native_job_id'])

    def publish_graph(self,p,run_id,kind,payload,*,evidence_origin):
        """Trusted producer ingestion, not an untrusted web upload or inference.

        Canonical graph contracts are executed, output is immutable in native CAS.
        Fixture/live origin must be supplied by the trusted producer; a label is
        provenance, not proof of pedagogic/real-book correctness.
        """
        from .graphs import validate_graph
        self.authorize(p,'publish'); ident(run_id)
        require(evidence_origin in ('SYNTHETIC_TEST','NATIVE_PRODUCER'),'invalid_evidence_origin',400)
        normalized = validate_graph(kind,payload)
        with self.catalog.tx() as db:
            _,body = self.catalog.intent(db,p,run_id)
            require(payload.get('source_hash')==body['source_hash'],'graph_source_mismatch')
            raw = canonical(dict(graph=normalized,source_hash=body['source_hash'],evidence_origin=evidence_origin))
            sha = hashlib.sha256(raw).hexdigest()
            existing = db.execute('SELECT sha FROM graphs WHERE run=? AND kind=?',(run_id,kind)).fetchone()
            require(existing is None or existing[0]==sha,'graph_immutable_conflict')
            with self.native(body) as native:
                artifact,_ = self._register(native,body,'operator.graph.'+kind,raw,
                    dict(source_hash=body['source_hash'],evidence_origin=evidence_origin,graph_kind=kind),evidence=True)
            if not existing:
                db.execute('INSERT INTO graphs VALUES(?,?,?,?)',(run_id,kind,artifact,sha))
                self.catalog.event(db,p.actor,'GRAPH_REGISTERED',run_id,dict(kind=kind,artifact_id=artifact,sha256=sha))
        return self.graph(p,run_id,kind)

    def graph(self,p,run_id,kind):
        from .graphs import validate_graph
        self.authorize(p,'read'); ident(run_id)
        require(kind in ('concept','prerequisite'),'invalid_graph_kind',400)
        with self.catalog.tx(read_only=True) as db:
            _,body = self.catalog.intent(db,p,run_id)
            row = db.execute('SELECT * FROM graphs WHERE run=? AND kind=?',(run_id,kind)).fetchone()
            if not row: return dict(status='NOT_RUN',reason='graph_producer_not_bound',kind=kind,nodes=[],edges=[],product_accepted=False)
            with self.native(body) as native:
                rec = native.persistence.load_artifact(row['artifact'])
                require(rec.run_id==body['native_job_id'] and rec.artifact_type=='operator.graph.'+kind and
                        rec.blob_digest==row['sha'],'graph_record_tampered')
                raw = native.cas.get_bytes(BlobRef(rec.blob_algorithm,rec.blob_digest,rec.blob_size))
            data = json.loads(raw)
            require(data['source_hash']==body['source_hash'],'graph_source_mismatch')
            graph = validate_graph(kind,dict(data['graph'],source_hash=data['source_hash']))
        return dict(status='AVAILABLE',kind=kind,artifact_id=row['artifact'],sha256=row['sha'],graph=graph,
                    source_id=body['source_id'],source_hash=body['source_hash'],
                    evidence_ref=row['artifact'],
                    evidence_origin=data['evidence_origin'],semantic_correctness_claimed=False,product_accepted=False)
