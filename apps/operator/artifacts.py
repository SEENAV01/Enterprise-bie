"""Persisted artifact/operator window over canonical stores and APIs.

The existing catalog's immutable bindings table is reused; no replacement
database, queue, worker or artifact store is introduced. Native source content
has no download/display route. Publication is a trusted producer Python port,
not an HTTP endpoint. SYNTHETIC_TEST remains visibly non-acceptance evidence.
"""
from dataclasses import asdict
import hashlib, json
from contextlib import contextmanager
from bie.infrastructure.artifact_api import ArtifactAPI
from bie.infrastructure.artifact_store import BlobRef, ArtifactCatalog, ArtifactRecord
from bie.infrastructure.persistence import PersistedArtifactRecord
from bie.infrastructure.evidence_api import EvidenceAPI
from .contracts import canonical, digest, require, ident as run_ident, strict_json, OperatorError, HASH
from .view_contracts import KINDS, MAX_DOCUMENT, validate_view, shape, text, ident

MAX_ARTIFACTS=2048
MAX_BLOB=25*1024*1024
MAX_CODE=256*1024
LANGUAGES={'python','javascript','typescript','tsx','jsx','css','html','json','text'}

def pagination(offset,limit):
    require(type(offset) is int and 0<=offset<=10000 and type(limit) is int and 1<=limit<=100,'invalid_pagination',400)

class ProductArtifacts:
    def __init__(self,service):self.s=service

    @contextmanager
    def context(self,p,run_id,permission='read'):
        self.s.authorize(p,permission);run_ident(run_id)
        with self.s.catalog.tx(read_only=permission=='read') as db:
            _,body=self.s.catalog.intent(db,p,run_id)
            with self.s.native(body) as native:
                self.s._snapshot(native,body)
                yield db,body,native

    def inventory(self,db,body,native):
        ids=native.persistence.artifacts_for_run(body['native_job_id'])
        require(len(ids)<=MAX_ARTIFACTS,'artifact_inventory_limit',429)
        records={key:native.persistence.load_artifact(key) for key in ids}
        for key,r in records.items():
            ident(key);require(r.artifact_id==key and r.run_id==body['native_job_id'] and r.blob_algorithm=='sha256'
                and HASH.fullmatch(r.blob_digest) and type(r.blob_size) is int and 0<=r.blob_size<=MAX_BLOB,'artifact_binding_invalid')
            require(len(r.parent_artifact_ids)<=200 and len(set(r.parent_artifact_ids))==len(r.parent_artifact_ids)
                and all(x in records for x in r.parent_artifact_ids),'artifact_parent_invalid')
            ident(r.stage_id);require(type(r.artifact_type) is str and 0<len(r.artifact_type)<=100 and
                all(c.isalnum() or c in '._-' for c in r.artifact_type),'artifact_binding_invalid')
        for binding in db.execute('SELECT kind,artifact,sha FROM graphs WHERE run=?',(body['run_id'],)):
            if not binding['kind'].startswith('artifact:'):continue
            r=records.get(binding['artifact']);require(r is not None and digest(asdict(r))==binding['sha'],'artifact_record_tampered')
        return records

    def canonical_api(self,records,native):
        class Catalog:
            def get(self,key):
                r=records.get(key)
                return None if r is None else dict(content_hash=r.blob_digest,artifact_id=key,artifact_type=r.artifact_type)
            def parents(self,key):return tuple(records[key].parent_artifact_ids)
        class Blobs:
            def get(self,sha):
                rows=[r for r in records.values() if r.blob_digest==sha]
                require(rows and len({r.blob_size for r in rows})==1,'artifact_inventory_inconsistent')
                r=rows[0];return native.cas.get_bytes(BlobRef(r.blob_algorithm,sha,r.blob_size))
        return ArtifactAPI(Catalog(),Blobs())

    def safe_meta(self,r,body):
        origin=r.metadata.get('evidence_origin','UNATTESTED_NATIVE_RECORD')
        if origin not in ('SYNTHETIC_TEST','NATIVE_PRODUCER'):origin='UNATTESTED_NATIVE_RECORD'
        return dict(artifact_id=r.artifact_id,artifact_type=r.artifact_type,sha256=r.blob_digest,size_bytes=r.blob_size,
            run_id=body['run_id'],native_run_id=r.run_id,stage_id=r.stage_id,evidence=r.evidence,
            parent_refs=r.parent_artifact_ids,origin=origin,integrity='METADATA_ONLY_UNTIL_CONTENT_VERIFIED',
            fixture_evidence=origin=='SYNTHETIC_TEST',attestation='NOT_VERIFIED',product_accepted=False)

    def browse(self,p,run_id,offset=0,limit=25,artifact_type=None,evidence_only=False):
        pagination(offset,limit);require(type(evidence_only) is bool,'invalid_filter',400)
        if artifact_type is not None:
            require(type(artifact_type) is str and len(artifact_type)<=100 and
                all(c.isalnum() or c in '._-' for c in artifact_type),'invalid_filter',400)
        with self.context(p,run_id) as (db,body,native):
            records=self.inventory(db,body,native)
            selected=sorted((r for r in records.values() if (artifact_type is None or r.artifact_type==artifact_type)
                              and (not evidence_only or r.evidence)),key=lambda r:r.artifact_id)
            page=selected[offset:offset+limit]
            return dict(items=[self.safe_meta(r,body) for r in page],total=len(selected),
                        next_offset=offset+limit if len(selected)>offset+limit else None)

    def publish(self,p,run_id,kind,payload,*,evidence_origin,parent_refs=()):
        require(kind in KINDS,'view_kind_unavailable',404)
        require(evidence_origin in ('SYNTHETIC_TEST','NATIVE_PRODUCER'),'invalid_evidence_origin',400)
        with self.context(p,run_id,'publish') as (db,body,native):
            projection,refs=validate_view(kind,payload,body)
            source='source-'+body['native_job_id'][4:]
            parents=sorted(set(parent_refs)|{source}|refs)
            require(len(parents)<=200,'artifact_parent_limit',400)
            records=self.inventory(db,body,native);api=self.canonical_api(records,native)
            for ref in parents:
                ident(ref);require(ref in records,'artifact_parent_invalid',400)
                api.content(ref)  # Verify every cited parent, not just a string.
            # Game provenance contains content hashes, not only reference IDs.
            stack=[payload]
            while stack:
                node=stack.pop()
                if type(node) is dict:
                    if node.get('$type')=='EvidenceRef' and 'content_sha256' in node:
                        require(records[node['artifact_id']].blob_digest==node['content_sha256'],'provenance_hash_mismatch',400)
                    stack.extend(node.values())
                elif type(node) in (list,tuple):stack.extend(node)
            envelope=dict(schema='bie.operator.view/1',kind=kind,source_hash=body['source_hash'],payload=payload,
                          evidence_origin=evidence_origin,producer_actor=p.actor)
            raw=canonical(envelope);require(len(raw)<=MAX_DOCUMENT,'view_size_limit',413)
            key='artifact:view:'+kind
            old=db.execute('SELECT * FROM graphs WHERE run=? AND kind=?',(run_id,key)).fetchone()
            if old:
                r=records[old['artifact']]
                require(api.content(r.artifact_id)==raw and r.parent_artifact_ids==parents,'view_immutable_conflict')
                return self._view(db,body,native,kind)
            require(len(records)<MAX_ARTIFACTS,'artifact_inventory_limit',429)
            blob=native.cas.put_bytes(raw)
            aid='opview-'+digest(dict(run=run_id,kind=kind,blob=blob.digest))
            rec=PersistedArtifactRecord(aid,'operator.view.'+kind,'sha256',blob.digest,blob.size,body['native_job_id'],
                'OPERATOR_VIEW',True,dict(evidence_origin=evidence_origin,source_hash=body['source_hash']),parents)
            # Recovery from a interrupted index write must never change parents.
            if aid in records:require(asdict(records[aid])==asdict(rec),'artifact_record_tampered')
            else:native.persistence.register_artifact(rec)
            db.execute('INSERT INTO graphs VALUES(?,?,?,?)',(run_id,key,aid,digest(asdict(rec))))
            self.s.catalog.event(db,p.actor,'ARTIFACT_BOUND',run_id,dict(kind=kind,artifact_id=aid,sha256=blob.digest))
            return self._view(db,body,native,kind)

    def _view(self,db,body,native,kind):
        require(kind in KINDS,'view_kind_unavailable',404)
        bound=db.execute('SELECT * FROM graphs WHERE run=? AND kind=?',(body['run_id'],'artifact:view:'+kind)).fetchone()
        if bound is None:return dict(kind=kind,status='NOT_RUN',reason='canonical_producer_artifact_not_bound',product_accepted=False)
        records=self.inventory(db,body,native);r=records[bound['artifact']]
        require(r.artifact_type=='operator.view.'+kind and r.blob_size<=MAX_DOCUMENT,'view_artifact_invalid')
        raw=self.canonical_api(records,native).content(r.artifact_id);wire=strict_json(raw,MAX_DOCUMENT)
        shape(wire,('schema','kind','source_hash','payload','evidence_origin','producer_actor'))
        require(wire['schema']=='bie.operator.view/1' and wire['source_hash']==body['source_hash'] and wire['kind']==kind,
                'view_source_mismatch')
        value,refs=validate_view(kind,wire['payload'],body)
        require(refs<=set(r.parent_artifact_ids),'view_parent_binding_invalid')
        for ref in r.parent_artifact_ids:self.canonical_api(records,native).content(ref)
        return dict(kind=kind,status='AVAILABLE',artifact_id=r.artifact_id,evidence_ref=r.artifact_id,sha256=r.blob_digest,
                    source_id=body['source_id'],source_hash=body['source_hash'],evidence_origin=wire['evidence_origin'],
                    fixture_evidence=wire['evidence_origin']=='SYNTHETIC_TEST',view=value,product_accepted=False,
                    validation='CANONICAL_CONTRACT_VALIDATED',semantic_correctness_claimed=False)

    def view(self,p,run_id,kind):
        with self.context(p,run_id) as args:return self._view(*args,kind)

    def lineage(self,p,run_id,artifact_id,max_nodes=128):
        ident(artifact_id);require(type(max_nodes) is int and 1<=max_nodes<=256,'invalid_lineage_limit',400)
        with self.context(p,run_id) as (db,body,native):
            records=self.inventory(db,body,native);require(artifact_id in records,'artifact_not_found',404)
            api=self.canonical_api(records,native);children={k:[] for k in records}
            for aid,r in records.items():
                for parent in r.parent_artifact_ids:children[parent].append(aid)
            # Bounded BFS gives all connected ancestors/descendants. Never silently
            # returns partial lineage as complete; cap overflow is an explicit error.
            pending=[artifact_id];selected=set()
            while pending:
                aid=pending.pop()
                if aid in selected:continue
                selected.add(aid);require(len(selected)<=max_nodes,'lineage_limit',413)
                pending.extend(api.lineage(aid));pending.extend(children[aid])
            cat=ArtifactCatalog(native.cas)
            cat.records={k:ArtifactRecord(k,r.artifact_type,BlobRef(r.blob_algorithm,r.blob_digest,r.blob_size),r.run_id,r.stage_id,
                r.parent_artifact_ids,r.evidence,r.metadata) for k,r in records.items() if k in selected}
            # Native cycle check and roots operate on the real selected inventory.
            roots=set()
            for aid in sorted(selected):
                try:roots.update(cat.trace_to_roots(aid))
                except ValueError:raise OperatorError('lineage_cycle') from None
                api.content(aid)
            return dict(artifact_id=artifact_id,nodes=[self.safe_meta(records[k],body)|{'integrity':'VERIFIED'} for k in sorted(selected)],
                edges=[dict(source=p,target=k,type='parent_of') for k in sorted(selected) for p in api.lineage(k)],
                roots=sorted(roots),complete=True,product_accepted=False)

    def evidence_detail(self,p,run_id,evidence_id):
        ident(evidence_id)
        with self.context(p,run_id) as (db,body,native):
            records=self.inventory(db,body,native);r=records.get(evidence_id)
            require(r is not None and r.evidence,'evidence_not_found',404)
            api=self.canonical_api(records,native);api.content(evidence_id)
            meta=self.safe_meta(r,body)|dict(integrity='VERIFIED',reviewer_state='UNATTESTED',signature_verified=False)
            if r.artifact_type.startswith('operator.view.'):
                kind=r.artifact_type.removeprefix('operator.view.')
                value=self._view(db,body,native,kind)
                require(value.get('artifact_id')==evidence_id,'evidence_binding_invalid')
                meta.update(evidence=dict(gate='CANONICAL_CONTRACT',status='VALIDATED_NOT_ACCEPTED',kind=kind),
                            source_hash=body['source_hash'])
            elif r.artifact_type=='document.inspection.evidence':
                # Existing safe decoder actually invokes canonical EvidenceAPI.
                document=strict_json(api.content(evidence_id),64*1024)
                allowed={'job_id','source_hash','status','diagnostic_code','result_blob_hash','result_byte_length','runtime_policy','page_count','total_blocks'}
                require(type(document) is dict and set(document)<=allowed and document.get('source_hash')==body['source_hash'],
                        'evidence_schema_invalid')
                from .service import SAFE_REASONS
                if 'diagnostic_code' in document and document['diagnostic_code'] not in SAFE_REASONS:document['diagnostic_code']='diagnostic_redacted'
                meta['evidence']=document
            else:meta['evidence']=dict(status='METADATA_ONLY',raw_evidence_not_exposed=True)
            class Store:
                def get(self,key):return meta if key==evidence_id else None
            return EvidenceAPI(Store()).get(evidence_id)

    def publish_code(self,p,run_id,code,language,*,evidence_origin,parent_refs=()):
        require(language in LANGUAGES,'code_language_unsupported',400)
        require(type(code) is str and len(code.encode('utf-8'))<=MAX_CODE,'code_size_limit',413)
        text(code,MAX_CODE)
        require(len(code.splitlines())<=10000,'code_line_limit',413)
        require(evidence_origin in ('SYNTHETIC_TEST','NATIVE_PRODUCER'),'invalid_evidence_origin',400)
        with self.context(p,run_id,'publish') as (db,body,native):
            records=self.inventory(db,body,native);parents=sorted(set(parent_refs)|{'source-'+body['native_job_id'][4:]})
            require(len(parents)<=200,'artifact_parent_limit',400)
            for ref in parents:
                ident(ref);require(ref in records,'artifact_parent_invalid',400);self.canonical_api(records,native).content(ref)
            raw=code.encode('utf-8');sha=hashlib.sha256(raw).hexdigest();aid='opcode-'+digest(dict(run=run_id,sha=sha,language=language))
            blob=native.cas.put_bytes(raw)
            rec=PersistedArtifactRecord(aid,'operator.generated_code','sha256',sha,blob.size,body['native_job_id'],'CODE',False,
                dict(language=language,evidence_origin=evidence_origin),parents)
            if aid in records:
                require(asdict(rec)==asdict(records[aid]),'code_immutable_conflict')
                bound=db.execute('SELECT * FROM graphs WHERE run=? AND kind=?',(run_id,'artifact:code:'+aid)).fetchone()
                if bound:return aid
            require(len(records)<MAX_ARTIFACTS,'artifact_inventory_limit',429)
            if aid not in records:native.persistence.register_artifact(rec)
            db.execute('INSERT INTO graphs VALUES(?,?,?,?)',(run_id,'artifact:code:'+aid,aid,digest(asdict(rec))))
            self.s.catalog.event(db,p.actor,'CODE_ARTIFACT_BOUND',run_id,dict(artifact_id=aid,sha256=sha))
            return aid

    def code(self,p,run_id,artifact_id,offset=0,limit=100):
        ident(artifact_id);pagination(offset,limit)
        with self.context(p,run_id) as (db,body,native):
            records=self.inventory(db,body,native);r=records.get(artifact_id)
            require(r is not None and r.artifact_type=='operator.generated_code','code_artifact_not_found',404)
            bound=db.execute('SELECT * FROM graphs WHERE run=? AND kind=?',(run_id,'artifact:code:'+artifact_id)).fetchone()
            require(bound is not None,'code_binding_missing')
            require(r.blob_size<=MAX_CODE and r.metadata.get('language') in LANGUAGES,'code_artifact_invalid')
            raw=self.canonical_api(records,native).content(artifact_id)
            try:decoded=raw.decode('utf-8')
            except UnicodeError:raise OperatorError('code_encoding_invalid') from None
            text(decoded,MAX_CODE);lines=decoded.splitlines()
            require(len(lines)<=10000,'code_line_limit',413)
            return self.safe_meta(r,body)|dict(integrity='VERIFIED',language=r.metadata['language'],line_count=len(lines),
                lines=[dict(number=n+1,text=lines[n]) for n in range(offset,min(offset+limit,len(lines)))],
                next_offset=offset+limit if len(lines)>offset+limit else None,executed=False,compiled=False)
