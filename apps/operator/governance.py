"""Versioned operator configuration over canonical policy/EVAL contracts.

The catalogue is an access/version index, not a second evaluator or engine.
Policy activation applies only to explicitly policy-bound *new* inspection runs.
Benchmark inputs are candidate-specific frozen snapshots; no score publication
or evaluation execution endpoint is exposed to the browser.
"""
from copy import deepcopy
from datetime import datetime
import json,re
from bie.infrastructure.policy_inheritance import policy_chain
from bie.infrastructure.audit_log import AuditLog
from bie.evaluation.benchmarks.release import gate,aggregation,thresholds,floors,domains
from bie.evaluation.benchmarks.release.ledger import ReleaseLedger
from bie.evaluation.benchmarks.models import BenchmarkError,digest as native_digest
from .catalog import timestamp
from .contracts import ident,require,digest,canonical,HASH,OperatorError

KINDS=('policy','benchmark')
MAX_CONFIGS=128;MAX_VERSIONS=256;MAX_EVENTS=65536

def integer(value,lo=0,hi=256):
    require(type(value) is int and lo<=value<=hi,'governance_integer_invalid',400);return value

def hash_value(value):
    require(type(value) is str and HASH.fullmatch(value),'governance_hash_invalid',400);return value

def shape(value,keys):require(type(value) is dict and set(value)==set(keys),'governance_schema_invalid',400)

def validate_policy(value,limit):
    shape(value,('model_policy','locale','deterministic','limits'))
    shape(value['limits'],('pdf_bytes',))
    require(value['model_policy']=='offline_only','live_policy_unbound',409)
    require(value['locale'] in ('en','hi') and value['deterministic'] is True,'policy_not_supported',400)
    integer(value['limits']['pdf_bytes'],1,limit)
    # Canonical inheritance is executed, not copied into the HTTP boundary.
    return policy_chain(dict(model_policy='offline_only',locale='en',deterministic=True,
                            limits={'pdf_bytes':limit}),value)

def validate_benchmark(value):
    shape(value,('manifest','policy'))
    require(len(canonical(value))<=16*1024,'governance_payload_limit',413)
    try:
        manifest,policy=value['manifest'],value['policy']
        cases=gate.validate_policy(policy,manifest)
        # validate_policy deliberately validates only some policy subcontracts.
        # Invoke their actual canonical validators with BLOCKED zero evidence so
        # invalid raters/floors/domain coverage cannot be saved as usable config.
        for row in cases.values():
            aggregation.aggregate(row['context'],[],policy['aggregation'],expected_policy_sha256=native_digest(policy['aggregation']))
        metrics=[dict(id=r['id'],status='BLOCKED',score='0') for r in policy['enterprise']['metrics']]
        thresholds.evaluate(policy['enterprise'],metrics,expected_policy_sha256=native_digest(policy['enterprise']))
        floor_ids={r['id'] for r in policy['critical_floors']['floors']}
        floors.evaluate(policy['critical_floors'],[r for r in metrics if r['id'] in floor_ids],
                       expected_policy_sha256=native_digest(policy['critical_floors']))
        domains.evaluate(policy['domains'],[dict(id=k,domain=r['context']['domain'],weight=r['weight'],
            leakage_group=r['leakage_group']) for k,r in cases.items()],
            [dict(id=k,status='BLOCKED',score='0') for k in cases],expected_policy_sha256=native_digest(policy['domains']))
    except (BenchmarkError,KeyError,TypeError,ValueError):raise OperatorError('benchmark_configuration_invalid',400) from None
    # Canonical identifier validators are intentionally broad. Bound any strings
    # exposed by this local UI to plain non-secret governed identifiers/numbers.
    def safe(v,depth=0):
        require(depth<=12,'governance_depth_limit',413)
        if type(v) is dict:
            require(len(v)<=64,'governance_collection_limit',413)
            for k,x in v.items():ident(k);safe(x,depth+1)
        elif type(v) is list:
            require(len(v)<=128,'governance_collection_limit',413)
            for x in v:safe(x,depth+1)
        elif type(v) is str:
            require(0<len(v)<=100 and bool(re.fullmatch(r'[A-Za-z0-9_.-]+|-?[0-9]+/[0-9]+',v,re.ASCII)),
                    'governance_text_invalid',400)
            require(not any(x in v.lower() for x in ('secret','password','bearer','sk-proj','api_key')),
                    'governance_secret_rejected',400)
        else:require(v is None or type(v) in (int,bool),'governance_value_invalid',400)
    safe(value)
    return deepcopy(value)

class Governance:
    def __init__(self,service):self.s=service

    def _event(self,db,p,action,target,details,before=None,after=None,authorization='ALLOW'):
        require(db.execute('SELECT COUNT(*) FROM audit').fetchone()[0]<MAX_EVENTS,'audit_capacity_reached',429)
        return self.s.catalog.event(db,p.actor,action,target,details,tenant=p.tenant,
            before_hash=before,after_hash=after,authorization=authorization)

    def authorize(self,p,permission,action,target):
        try:self.s.authorize(p,permission)
        except OperatorError as e:
            if e.code=='forbidden':
                # Known currently valid principal only. No credential, submitted
                # payload, exception string or attacker-chosen path is recorded.
                self.s.authorize(p,'admin_read')
                with self.s.catalog.tx() as db:self._event(db,p,'CONFIG_DENIED',ident(target),
                    {'action':action},authorization='DENY')
            raise

    def _kind(self,kind):require(kind in KINDS,'governance_kind_invalid',400)

    def _version(self,db,p,kind,id,revision):
        row=db.execute('SELECT body FROM governance_versions WHERE tenant=? AND kind=? AND id=? AND revision=?',
                       (p.tenant,kind,id,revision)).fetchone()
        require(row is not None,'configuration_not_found',404)
        return json.loads(row[0])

    def _active(self,db,p,kind):
        row=db.execute('SELECT body FROM governance_active WHERE tenant=? AND kind=?',(p.tenant,kind)).fetchone()
        return json.loads(row[0]) if row else None

    def save(self,p,kind,id,configuration,expected_revision,key):
        self._kind(kind);ident(id);ident(key);integer(expected_revision)
        self.authorize(p,'admin_config','SAVE_'+kind.upper(),id)
        configuration=validate_policy(configuration,self.s.limit) if kind=='policy' else validate_benchmark(configuration)
        key_hash=digest({'tenant':p.tenant,'key':key})
        fingerprint=digest({'kind':kind,'id':id,'configuration':configuration,'expected_revision':expected_revision})
        with self.s.catalog.tx() as db:
            self.s.authorize(p,'admin_config')
            rows=[json.loads(r[0]) for r in db.execute('SELECT body FROM governance_versions WHERE tenant=? AND kind=? AND id=? ORDER BY revision',
                        (p.tenant,kind,id))]
            for row in rows:
                if row['key_hash']==key_hash:
                    require(row['request_sha256']==fingerprint,'idempotency_conflict')
                    return dict(row,replayed=True)
            require(len(rows)==expected_revision,'stale_configuration_revision')
            require(len(rows)<MAX_VERSIONS,'configuration_version_limit',429)
            require(rows or db.execute('SELECT COUNT(DISTINCT id) FROM governance_versions WHERE tenant=? AND kind=?',
                (p.tenant,kind)).fetchone()[0]<MAX_CONFIGS,'configuration_catalog_full',429)
            row=dict(kind=kind,config_id=id,revision=len(rows)+1,configuration=configuration,
                configuration_sha256=digest(configuration),created_at=timestamp(),actor=p.actor,
                key_hash=key_hash,request_sha256=fingerprint,
                previous_sha256=rows[-1]['configuration_sha256'] if rows else None)
            db.execute('INSERT INTO governance_versions VALUES(?,?,?,?,?)',(p.tenant,kind,id,row['revision'],canonical(row).decode()))
            self._event(db,p,'CONFIG_VERSION_CREATED',id,{'kind':kind,'revision':row['revision']},
                before=row['previous_sha256'],after=row['configuration_sha256'])
        return dict(row,replayed=False)

    def activate(self,p,kind,id,revision,sha,expected_active_sha,key):
        self._kind(kind);ident(id);ident(key);integer(revision,1);hash_value(sha)
        if expected_active_sha is not None:hash_value(expected_active_sha)
        self.authorize(p,'admin_config','ACTIVATE_'+kind.upper(),id)
        key_hash=digest({'tenant':p.tenant,'key':key})
        request_sha=digest(dict(kind=kind,id=id,revision=revision,sha=sha,previous=expected_active_sha))
        with self.s.catalog.tx() as db:
            self.s.authorize(p,'admin_config');version=self._version(db,p,kind,id,revision)
            require(version['configuration_sha256']==sha,'configuration_pin_mismatch')
            old=self._active(db,p,kind)
            # Activation receipts remain append-only; replaying an OLD activation
            # must never overwrite a newer active version or falsely call it active.
            for r in db.execute('SELECT body FROM audit ORDER BY n'):
                b=json.loads(r[0]);d=b.get('details',{})
                if b.get('tenant')==p.tenant and b['action']=='CONFIG_ACTIVATED' and d.get('key_hash')==key_hash:
                    require(d['request_sha256']==request_sha,'idempotency_conflict')
                    return dict(replayed=True,requested=dict(config_id=id,revision=revision,configuration_sha256=sha),
                        active=old,requested_is_active=bool(old and old['config_id']==id and old['revision']==revision))
            require((old['activation_sha256'] if old else None)==expected_active_sha,'stale_activation')
            active=dict(config_id=id,revision=revision,configuration_sha256=sha,activated_at=timestamp(),
                        actor=p.actor,kind=kind)
            active['activation_sha256']=digest(active)
            db.execute('INSERT OR REPLACE INTO governance_active VALUES(?,?,?)',(p.tenant,kind,canonical(active).decode()))
            self._event(db,p,'CONFIG_ACTIVATED',id,dict(kind=kind,revision=revision,key_hash=key_hash,request_sha256=request_sha),
                before=old['activation_sha256'] if old else None,after=active['activation_sha256'])
        return dict(replayed=False,active=active,requested_is_active=True)

    def history(self,p,kind,id,after=0,limit=25):
        self.s.authorize(p,'admin_read');self._kind(kind);ident(id);integer(after);integer(limit,1,50)
        with self.s.catalog.tx(read_only=True) as db:
            rows=[json.loads(r[0]) for r in db.execute('SELECT body FROM governance_versions WHERE tenant=? AND kind=? AND id=? AND revision>? ORDER BY revision LIMIT ?',
                (p.tenant,kind,id,after,limit+1))]
            if not rows:self._version(db,p,kind,id,1)
            return dict(items=[self.public(r) for r in rows[:limit]],active=self._active(db,p,kind),
                next_revision=rows[limit-1]['revision'] if len(rows)>limit else None,product_accepted=False)

    def public(self,row):return {k:v for k,v in row.items() if k not in ('key_hash','request_sha256')}

    def list(self,p,kind,after=None,limit=25):
        self.s.authorize(p,'admin_read');self._kind(kind);integer(limit,1,50)
        if after is not None:ident(after)
        with self.s.catalog.tx(read_only=True) as db:
            ids=[r[0] for r in db.execute('SELECT DISTINCT id FROM governance_versions WHERE tenant=? AND kind=? AND id>? ORDER BY id LIMIT ?',
                (p.tenant,kind,after or '',limit+1))]
            items=[]
            for id in ids[:limit]:
                r=db.execute('SELECT body FROM governance_versions WHERE tenant=? AND kind=? AND id=? ORDER BY revision DESC LIMIT 1',
                    (p.tenant,kind,id)).fetchone();items.append(self.public(json.loads(r[0])))
            return dict(kind=kind,status='CONFIGURED' if items else 'NOT_CONFIGURED',items=items,
                active=self._active(db,p,kind),next_after=ids[limit-1] if len(ids)>limit else None,
                can_configure='admin_config' in p.permissions,execution_status='NOT_RUN',
                consumer_scope='EXPLICIT_POLICY_BOUND_NEW_INSPECTION_RUNS' if kind=='policy' else 'FROZEN_NATIVE_RELEASE_LEDGER_INPUTS',
                release_authorized=False,product_accepted=False)

    def diff(self,p,kind,id,left,right):
        self.s.authorize(p,'admin_read');self._kind(kind);ident(id);integer(left,1);integer(right,1)
        with self.s.catalog.tx(read_only=True) as db:
            a=self._version(db,p,kind,id,left);b=self._version(db,p,kind,id,right)
        changes=[]
        def walk(x,y,path):
            if type(x) is dict and type(y) is dict:
                for k in sorted(set(x)|set(y)):walk(x.get(k),y.get(k),path+'/'+k)
            elif x!=y:changes.append(dict(path=path,before=x,after=y))
        walk(a['configuration'],b['configuration'],'')
        return dict(config_id=id,left_sha256=a['configuration_sha256'],right_sha256=b['configuration_sha256'],changes=changes)

    def binding(self,db,p,id,revision,sha):
        ident(id);integer(revision,1);hash_value(sha)
        v=self._version(db,p,'policy',id,revision);active=self._active(db,p,'policy')
        require(active and active['config_id']==id and active['revision']==revision and v['configuration_sha256']==sha,
                'policy_not_active')
        return v

    def execute_benchmark(self,p,id,revision,sha,ledger,campaign_id,attempt_id,assessments,**kwargs):
        """Trusted producer port: actual canonical ledger; never HTTP score input."""
        self.s.authorize(p,'publish');ident(id);integer(revision,1);hash_value(sha)
        require(type(ledger) is ReleaseLedger,'native_release_ledger_required',400)
        with self.s.catalog.tx(read_only=True) as db:
            version=self._version(db,p,'benchmark',id,revision);active=self._active(db,p,'benchmark')
            require(active and active['config_id']==id and active['revision']==revision and
                    version['configuration_sha256']==sha,'benchmark_not_active')
        c=version['configuration'];self.s.authorize(p,'publish')
        return ReleaseLedger.execute(ledger,campaign_id=campaign_id,attempt_id=attempt_id,
            manifest=c['manifest'],policy=c['policy'],assessments=assessments,
            expected_manifest_sha256=native_digest(c['manifest']),expected_policy_sha256=native_digest(c['policy']),**kwargs)

    def _tenant(self,db,body):
        if 'tenant' in body:return body['tenant']
        # Exact resource ownership only; providers may share a config ID across
        # tenants. Ambiguous legacy records are omitted, never actor-inferred.
        owners=set()
        for table,column in (('sources','id'),('intents','id'),('workers','id'),('provider_versions','id')):
            owners.update(r[0] for r in db.execute('SELECT DISTINCT tenant FROM '+table+' WHERE '+column+'=?',(body['target'],)))
        return next(iter(owners)) if len(owners)==1 else None

    def audit(self,p,after=0,limit=25,action=None,target=None):
        self.s.authorize(p,'admin_read');integer(after,0,MAX_EVENTS);integer(limit,1,50)
        if action is not None:ident(action)
        if target is not None:ident(target)
        items=[];scan_after=after;more=False;native=AuditLog()
        with self.s.catalog.tx(read_only=True) as db:
            # Bounded traversal per request, independently of visible tenants.
            rows=db.execute('SELECT * FROM audit WHERE n>? ORDER BY n LIMIT 257',(after,)).fetchall()
            for row in rows[:256]:
                b=json.loads(row['body']);scan_after=row['n']
                if self._tenant(db,b)!=p.tenant or (action and b['action']!=action) or (target and b['target']!=target):continue
                ident(b['actor']);ident(b['action']);ident(b['target'])
                when=datetime.fromisoformat(b['timestamp']);require(when.tzinfo is not None,'audit_timestamp_invalid')
                # The canonical in-memory log verifies the safe projection only;
                # Catalog.verify already verified the authoritative durable chain.
                entry=native.append(b['actor'],b['action'],b['target'],when.timestamp())
                items.append(dict(sequence=row['n'],actor=b['actor'],action=b['action'],target=b['target'],timestamp=b['timestamp'],
                    authorization=b.get('authorization','LEGACY_NOT_RECORDED'),
                    before_sha256=b.get('before_hash'),after_sha256=b.get('after_hash'),
                    receipt_sha256=row['sha'],details_sha256=digest(b['details']),
                    details_exposed=False,canonical_projection_sha256=entry.entry_hash,
                    tenant_attribution='EXPLICIT' if 'tenant' in b else 'EXACT_RESOURCE_BINDING'))
                if len(items)==limit:
                    more=True;break
            require(AuditLog.verify(native),'canonical_audit_projection_invalid')
            more=more or len(rows)>256
        return dict(items=items,next_after=scan_after if more else None,
            status='VERIFIED_HISTORY' if items else 'EMPTY',durable_chain_verified=True,
            legacy_unattributable_entries='OMITTED_FAIL_CLOSED',privileged_rewrite_protected=False,
            external_notarization=False,product_accepted=False)
