"""HARD-001/002: typed terminal report, scoped time and immutable-fact checking.

All terminal bytes are read by the existing verified SnapshotStore. This is an
assessment-evidence validator, not a semantic evaluator or source of trust. A
matching signed report may still be wrong; operational assessors remain separate.
"""
from dataclasses import dataclass
from .contracts import strict_json
from .report_policy import TERMINAL_SCHEMA, FACT_SCHEMA, LEDGER_SCHEMA
from ..release_v2.contracts import ContractError, token, integer, choice
from ..release_v2.codec import artifact_from_dict
from ..release_v2.diagnostics import Diagnostic

BAD_STATUSES=('FAIL','FAILED','ERROR','SKIPPED','NOT_RUN','REVIEW_REQUIRED','PENDING','BLOCKED','CONTRACT_ONLY')
KNOWN_COLLECTIONS=('gaps','batch017_open_obligations','batch018_open_obligations',
                   'batch019_open_obligations','batch020_open_obligations','audit001_findings')
CLOSED=('CLOSED','RESOLVED','VERIFIED_CLOSED')
OPEN=('OPEN','EXTERNAL_PENDING','PARTIALLY_ADDRESSED_OPEN','PENDING','BLOCKED')


def fields(value, required, optional=()):
    if type(value) is not dict or not set(required)<=set(value) or not set(value)<=set(required)|set(optional):
        raise ContractError('TERMINAL_FIELDS')
    return value


def array(value, name, limit=4096):
    if type(value) is not list or len(value)>limit:
        raise ContractError('TERMINAL_ARRAY',name)
    return value


def nonblank(value, field, limit=16384):
    if type(value) is not str or not value.strip() or len(value)>limit:
        raise ContractError('TERMINAL_TEXT',field)


@dataclass(frozen=True)
class TerminalContext:
    candidate: object
    release_policy_digest: str
    bundle_digest: str | None
    subject_type: str
    subject_id: str
    evidence_id: str
    inspected_artifacts: tuple
    as_of: int
    parent_created_at: int
    parent_expires_at: int
    max_lifetime: int
    mode: str


@dataclass(frozen=True)
class TerminalResult:
    blockers: tuple[str,...]
    advisories: tuple[str,...]
    expires_at: int | None


def ledger_blockers(raw, inspect):
    """Closed ledger adapters, including every historical Section16 collection.

    This detects supplied unresolved obligations. Authoritative inventory completeness
    and independently approved closure evidence remain HARD-006 (not string inference).
    """
    codes=set()
    schema=raw.get('schema_version') if type(raw)is dict else None
    if schema==LEDGER_SCHEMA:
        fields(raw,('schema_version','collections'))
        collections=array(raw['collections'],'collections',128);seen=set();rows=[]
        for col in collections:
            fields(col,('collection_id','items'));token(col['collection_id'],'collection_id')
            if col['collection_id']in seen:raise ContractError('DUPLICATE_OBLIGATION_COLLECTION')
            seen.add(col['collection_id'])
            rows.extend(array(col['items'],'items'))
        seen_ids=set()
        for row in rows:
            fields(row,('obligation_id','status','closure_artifact'))
            token(row['obligation_id'],'obligation_id')
            if row['obligation_id']in seen_ids:raise ContractError('DUPLICATE_OBLIGATION_ID')
            seen_ids.add(row['obligation_id'])
            choice(row['status'],CLOSED+OPEN,'obligation.status')
            if row['status']not in CLOSED:codes.add('SOURCE_REPORT_OPEN_GAPS')
            elif row['closure_artifact']is None:codes.add('OBLIGATION_CLOSURE_EVIDENCE_MISSING')
            else:inspect(artifact_from_dict(row['closure_artifact']))
    elif schema=='1.0.0':
        # Snapshot format is registered only for the exact known collection grammar.
        fields(raw,('schema_version','scope','gaps'),KNOWN_COLLECTIONS[1:])
        nonblank(raw['scope'],'ledger.scope')
        seen_ids=set()
        for col in KNOWN_COLLECTIONS:
            if col not in raw:continue
            for row in array(raw[col],col):
                allowed={'id','gap_id','status','title','description','requirement','owner_or_next_work',
                         'priority','hardening_task_ids','closure_artifact'}|{f'batch{i:03}_update' for i in range(1,23)}
                if type(row)is not dict or not set(row)<=allowed or 'status'not in row:
                    raise ContractError('OBLIGATION_FIELDS')
                ids=[row[x] for x in ('id','gap_id') if x in row]
                if len(ids)!=1:raise ContractError('OBLIGATION_ID')
                token(ids[0],'obligation_id')
                if ids[0]in seen_ids:raise ContractError('DUPLICATE_OBLIGATION_ID')
                seen_ids.add(ids[0]);choice(row['status'],CLOSED+OPEN,'obligation.status')
                for k,v in row.items():
                    if k=='hardening_task_ids':
                        for ident in array(v,k,128):token(ident,k)
                    elif k not in ('closure_artifact',):nonblank(v,k)
                if row['status']not in CLOSED:codes.add('SOURCE_REPORT_OPEN_GAPS')
                elif not row.get('closure_artifact'):codes.add('OBLIGATION_CLOSURE_EVIDENCE_MISSING')
                else:inspect(artifact_from_dict(row['closure_artifact']))
        # Legacy ledger carries no run/time/identity: it can veto, never authorize.
        codes.add('LEGACY_LEDGER_NOT_BOUND_TERMINAL')
    else:raise ContractError('UNREGISTERED_LEDGER_SCHEMA')
    return codes


def validate_terminal(raw, context, requirement, inspect):
    """inspect(ref) must register aliases, read/hash bytes, and retain graph edges."""
    if type(raw)is not dict:raise ContractError('TERMINAL_OBJECT')
    schema=raw.get('schema_version')
    if schema==FACT_SCHEMA:raise ContractError('TIMELESS_FACT_NOT_GATE_PROOF')
    if schema in ('1.0.0',LEDGER_SCHEMA):
        codes=ledger_blockers(raw,inspect);codes.add('LEDGER_NOT_GATE_PROOF')
        return TerminalResult(tuple(sorted(codes)),(),None)
    if schema!=TERMINAL_SCHEMA:raise ContractError('UNREGISTERED_TERMINAL_SCHEMA')
    fields(raw,('schema_version','report_id','status','scope','binding','captured_at','created_at','expires_at',
                'checks','diagnostics','ledgers','immutable_facts'))
    token(raw['report_id'],'report_id')
    choice(raw['scope'],('NATIVE_PRODUCT','DIAGNOSTIC'),'terminal.scope')
    codes=set();advisories=set()
    if context.mode=='production' and raw['scope']!='NATIVE_PRODUCT':codes.add('SYNTHETIC_SOURCE_REPORT')
    choice(raw['status'],('PASS',)+BAD_STATUSES,'terminal.status')
    if raw['status']!='PASS':codes.add('SOURCE_REPORT_NOT_CLEAR')
    if requirement is None:raise ContractError('TERMINAL_POLICY_UNCONFIGURED')
    binding=fields(raw['binding'],('subject_type','subject_id','evidence_id','candidate_digest','run_id','revision',
                    'release_policy_digest','evaluator_policy_digest','bundle_digest','inspected_artifacts'))
    candidate=context.candidate
    expected=dict(subject_type=context.subject_type,subject_id=context.subject_id,evidence_id=context.evidence_id,
        candidate_digest=candidate.content_digest,run_id=candidate.run_id,revision=candidate.revision,
        release_policy_digest=context.release_policy_digest,evaluator_policy_digest=requirement.evaluator_policy_digest,
        bundle_digest=context.bundle_digest)
    for key,val in expected.items():
        if type(binding[key])is not type(val) or binding[key]!=val:codes.add('TERMINAL_BINDING_MISMATCH')
    inspected=tuple(artifact_from_dict(x) for x in array(binding['inspected_artifacts'],'inspected_artifacts',2048))
    if len({x.artifact_id for x in inspected})!=len(inspected) or len({x.path for x in inspected})!=len(inspected):
        raise ContractError('TERMINAL_INSPECTED_DUPLICATE')
    if set(inspected)!=set(context.inspected_artifacts):codes.add('TERMINAL_INSPECTED_BINDING_MISMATCH')
    for ref in inspected:inspect(ref)
    captured=integer(raw['captured_at'],'terminal.captured_at')
    created=integer(raw['created_at'],'terminal.created_at');expires=integer(raw['expires_at'],'terminal.expires_at',created+1)
    if captured>created:codes.add('TERMINAL_CAPTURE_AFTER_CREATION')
    if context.as_of-captured>context.max_lifetime:codes.add('STALE_TERMINAL_CAPTURE')
    if created>context.as_of:codes.add('FUTURE_TERMINAL_EVIDENCE')
    if expires<=context.as_of:codes.add('EXPIRED_TERMINAL_EVIDENCE')
    if expires-created>context.max_lifetime:codes.add('TERMINAL_LIFETIME_EXCEEDED')
    # A wrapper cannot claim to have assessed a terminal that did not exist yet.
    if created>context.parent_created_at:codes.add('TERMINAL_AFTER_WRAPPER')
    seen=set();budget=[0]
    def diagnostics(values):
        local=set()
        for value in array(values,'diagnostics',128):
            item=Diagnostic.from_dict(value)
            if item.code in local:raise ContractError('DUPLICATE_TERMINAL_DIAGNOSTIC')
            local.add(item.code)
            if item.severity=='BLOCKING':codes.update(('SOURCE_REPORT_NOT_CLEAR',item.code))
            else:advisories.add(item.code)
    def checks(values,depth=0):
        if depth>24:raise ContractError('TERMINAL_CHECK_DEPTH')
        for check in array(values,'checks'):
            budget[0]+=1
            if budget[0]>4096:raise ContractError('TERMINAL_CHECK_LIMIT')
            fields(check,('check_id','status','diagnostics','checks'))
            token(check['check_id'],'check_id')
            if check['check_id']in seen:raise ContractError('DUPLICATE_TERMINAL_CHECK')
            seen.add(check['check_id'])
            choice(check['status'],('PASS',)+BAD_STATUSES,'terminal.check.status')
            if check['status']!='PASS':codes.add('SOURCE_REPORT_NOT_CLEAR')
            diagnostics(check['diagnostics']);checks(check['checks'],depth+1)
    diagnostics(raw['diagnostics']);checks(raw['checks'])
    if not seen:codes.add('EMPTY_TERMINAL_CHECKS')
    if not set(requirement.required_check_ids)<=seen:codes.add('MISSING_REQUIRED_TERMINAL_CHECK')
    ledger_ids=set()
    for value in array(raw['ledgers'],'ledgers',128):
        ref=artifact_from_dict(value)
        if ref.role!='report' or ref.artifact_id in ledger_ids:raise ContractError('TERMINAL_LEDGER_REFERENCE')
        ledger_ids.add(ref.artifact_id);codes.update(ledger_blockers(strict_json(inspect(ref)),inspect))
    fact_ids=set()
    for fact in array(raw['immutable_facts'],'immutable_facts',128):
        fields(fact,('schema_version','fact_kind','artifact','justification'))
        if fact['schema_version']!=FACT_SCHEMA or fact['fact_kind']!='artifact_identity':raise ContractError('IMMUTABLE_FACT_SCHEMA')
        nonblank(fact['justification'],'immutable_fact.justification')
        ref=artifact_from_dict(fact['artifact'])
        if ref.artifact_id in fact_ids:raise ContractError('IMMUTABLE_FACT_DUPLICATE')
        fact_ids.add(ref.artifact_id);inspect(ref)
    return TerminalResult(tuple(sorted(codes)),tuple(sorted(advisories)),expires)
