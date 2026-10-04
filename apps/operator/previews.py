"""Artifact-bound preview adapter, not a renderer/game compiler or release gate.

Producer publication is Python-only. Native decoding and package validation are
delegated to unchanged BIE implementations. Injected decoding is permanently
labelled synthetic; it cannot issue native evidence. Preview grants are scoped,
short-lived, process-local and independently revocable. They confer no API access.
"""
from contextlib import contextmanager
from dataclasses import asdict
from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib, json, re, secrets, threading, time
from html.parser import HTMLParser
from bie.infrastructure.persistence import PersistedArtifactRecord
from bie.compiler.render_contracts import RenderReceipt
from bie.qa.video_v2.media import inspect_bytes, DecodedVideo
from bie.qa.video_v2.models import VideoPolicy
from bie.qa.release_v2.contracts import ContractError
from bie.game_engine.build_runtime_engine.contracts import RuntimePackageManifest, PackageArtifact, safe_relative
from bie.game_engine.build_runtime_engine.integrity import verify_package, verify_compiler_binding
from bie.game_engine.build_runtime_engine.module_graph import verify_module_graph
from bie.game_engine.build_runtime_engine.entrypoint import ENTRY_JS
from bie.game_engine.canonical import fingerprint
from .artifacts import ProductArtifacts, MAX_BLOB, MAX_ARTIFACTS
from .contracts import canonical, digest, require, OperatorError, strict_json, private_path

MAX_FILES=128
MAX_GAME_BYTES=25_000_000
MAX_FILE_BYTES=5_000_000
MAX_GRANTS=128
MIME={'.html':'text/html','.js':'text/javascript','.json':'application/json',
      '.css':'text/css','.png':'image/png','.jpg':'image/jpeg','.wav':'audio/wav','.mp3':'audio/mpeg','.txt':'text/plain'}

def sha(raw):return hashlib.sha256(raw).hexdigest()

def byte_range(value,size,etag,if_range=None):
    """RFC9110 single byte range; multipart is deliberately not implemented."""
    if value is None or (if_range is not None and if_range!=etag):return 0,size-1,200
    require(type(value) is str and len(value)<=100,'range_not_satisfiable',416)
    m=re.fullmatch(r'bytes=(\d{0,20})-(\d{0,20})',value)
    require(m is not None and any(m.groups()) and size>0,'range_not_satisfiable',416)
    a,b=m.groups()
    if not a:
        n=int(b);require(n>0,'range_not_satisfiable',416);start,end=max(0,size-n),size-1
    else:
        start=int(a);end=min(size-1,int(b)) if b else size-1
    require(start<size and end>=start,'range_not_satisfiable',416)
    return start,end,206

class ClosedHtml(HTMLParser):
    def __init__(self,files):super().__init__(convert_charrefs=True);self.files=files;self.scripts=[];self.in_script=False
    def handle_starttag(self,tag,attrs):
        values=dict(attrs);require(len(values)==len(attrs),'game_html_invalid')
        require(tag not in ('iframe','object','embed','form','base','link'),'game_html_active_content')
        require(not any(k.startswith('on') or k in ('srcdoc','action') for k in values),'game_html_active_content')
        if tag=='meta':require(values.get('http-equiv','').lower()!='refresh','game_html_active_content')
        for key in ('src','href','poster'):
            if key in values:
                v=values[key];require(type(v) is str and v.startswith('./') and 'runtime/'+v[2:] in self.files,'game_html_external_resource')
        if tag=='script':
            require(values=={'type':'module','src':'./entry.js'},'game_html_script_invalid')
            self.scripts.append(values['src']);self.in_script=True
    def handle_endtag(self,tag):
        if tag=='script':self.in_script=False
    def handle_data(self,data):
        require(not self.in_script or not data.strip(),'game_html_inline_script')

class Previews:
    def __init__(self,service,clock=time.monotonic):
        self.s=service;self.art=ProductArtifacts(service);self.clock=clock
        self._grants={};self._lock=threading.Lock()

    def _publish(self,p,run_id,kind,info,files,origin,source_hash):
        require(kind in ('render','game') and origin in ('NATIVE_PRODUCER','SYNTHETIC_TEST'),'preview_kind_invalid')
        require(type(files) is dict and 1<=len(files)<=MAX_FILES,'preview_inventory_limit',413)
        require(all(type(v) is bytes and 0<len(v)<=MAX_BLOB for v in files.values()),'preview_file_limit',413)
        require(sum(map(len,files.values()))<=MAX_BLOB,'preview_package_limit',413)
        with self.art.context(p,run_id,'publish') as (db,body,native):
            require(source_hash==body['source_hash'],'preview_source_mismatch')
            records=self.art.inventory(db,body,native)
            require(len(records)+len(files)+1<=MAX_ARTIFACTS,'artifact_inventory_limit',429)
            source='source-'+body['native_job_id'][4:]
            self.art.canonical_api(records,native).content(source)
            envelope=dict(schema='bie.operator.preview/1',kind=kind,source_hash=body['source_hash'],origin=origin,
                          info=info,files={path:dict(sha256=sha(raw),size_bytes=len(raw)) for path,raw in sorted(files.items())})
            envelope['artifact_ids']={path:'opmedia-'+digest(dict(run=run_id,kind=kind,path=path,sha=sha(raw))) for path,raw in sorted(files.items())}
            raw=canonical(envelope);require(len(raw)<=256*1024,'preview_manifest_limit',413)
            key='artifact:preview:'+kind
            previous=db.execute('SELECT * FROM graphs WHERE run=? AND kind=?',(run_id,key)).fetchone()
            if previous:
                old=self.art.canonical_api(records,native).content(previous['artifact'])
                require(old==raw,'preview_immutable_conflict')
                return self._read(db,body,native,kind)[0]
            parents=[source];content_ids={}
            for path,data in sorted(files.items()):
                blob=native.cas.put_bytes(data);aid='opmedia-'+digest(dict(run=run_id,kind=kind,path=path,sha=blob.digest))
                rec=PersistedArtifactRecord(aid,'operator.preview.file','sha256',blob.digest,blob.size,body['native_job_id'],
                    'PREVIEW',False,dict(evidence_origin=origin,source_hash=body['source_hash']),[source])
                if aid in records:require(asdict(records[aid])==asdict(rec),'preview_record_tampered')
                else:native.persistence.register_artifact(rec)
                bind='artifact:preview-file:'+aid
                old=db.execute('SELECT * FROM graphs WHERE run=? AND kind=?',(run_id,bind)).fetchone()
                if old:require(old['artifact']==aid and old['sha']==digest(asdict(rec)),'preview_record_tampered')
                else:db.execute('INSERT INTO graphs VALUES(?,?,?,?)',(run_id,bind,aid,digest(asdict(rec))))
                parents.append(aid);content_ids[path]=aid
            # The manifest includes the logical-path to actual canonical artifact linkage.
            envelope['artifact_ids']=content_ids;raw=canonical(envelope)
            blob=native.cas.put_bytes(raw);aid='oppreview-'+digest(dict(run=run_id,kind=kind,sha=blob.digest))
            rec=PersistedArtifactRecord(aid,'operator.preview.'+kind,'sha256',blob.digest,blob.size,body['native_job_id'],
                'PREVIEW',True,dict(evidence_origin=origin,source_hash=body['source_hash']),sorted(parents))
            if aid in records:require(asdict(records[aid])==asdict(rec),'preview_record_tampered')
            else:native.persistence.register_artifact(rec)
            db.execute('INSERT INTO graphs VALUES(?,?,?,?)',(run_id,key,aid,digest(asdict(rec))))
            self.s.catalog.event(db,p.actor,'PREVIEW_BOUND',run_id,dict(kind=kind,artifact_id=aid,sha256=blob.digest))
            return self._read(db,body,native,kind)[0]

    def publish_render(self,p,run_id,data,receipt,policy,*,source_hash,tools=None,decoder=None):
        self.s.authorize(p,'publish')
        require(type(data) is bytes and 0<len(data)<=MAX_BLOB,'preview_file_limit',413)
        require(type(receipt) is RenderReceipt and type(policy) is VideoPolicy,'render_contract_required',400)
        require(receipt.passed is True and receipt.accepted is False and receipt.failure_code is None and not receipt.errors
            and receipt.mode=='full' and receipt.process_started is True and receipt.media is not None
            and receipt.artifact_sha256==sha(data) and receipt.artifact_size_bytes==len(data)
            and receipt.expected_frames==policy.expected_frames and receipt.composition_id==policy.composition_id
            and receipt.input_sha256==policy.expected_input_digest and type(receipt.recipe_sha256) is str
            and re.fullmatch('[a-f0-9]{64}',receipt.recipe_sha256) is not None,
            'render_receipt_invalid')
        origin='SYNTHETIC_TEST' if decoder is not None else 'NATIVE_PRODUCER'
        require(receipt.execution_kind==('INJECTED_TEST_RUNNER' if decoder is not None else 'LOCAL_REMOTION_CLI'),
                'render_execution_kind_invalid')
        try:decoded=(decoder or inspect_bytes)(data,policy,tools)
        except ContractError as exc:
            if exc.code in ('VIDEO_POSIX_WORKER_REQUIRED','VIDEO_TOOL_UNAVAILABLE'):
                raise OperatorError('native_media_worker_unavailable',503) from None
            raise OperatorError('media_validation_failed') from None
        require(type(decoded) is DecodedVideo and decoded.frames_count==policy.expected_frames
            and decoded.width==policy.width and decoded.height==policy.height and decoded.codec in policy.codecs
            and decoded.pixel_format in policy.pixel_formats and decoded.fps==Fraction(policy.fps_numerator,policy.fps_denominator)
            and (not policy.require_audio or decoded.audio_streams>0),'render_decode_mismatch')
        duration=(decoded.pts[-1]+decoded.durations[-1]-decoded.pts[0])*decoded.time_base
        require(duration>0 and abs(duration-Fraction(decoded.frames_count,1)/decoded.fps)<=Fraction(1,100),
                'render_duration_mismatch')
        require((receipt.media.width,receipt.media.height,receipt.media.decoded_frames,receipt.media.codec_name,receipt.media.pixel_format,
                 receipt.media.audio_streams)==(decoded.width,decoded.height,decoded.frames_count,decoded.codec,decoded.pixel_format,decoded.audio_streams)
                and receipt.media.fps==float(decoded.fps) and abs(receipt.media.duration_s-float(duration))<.01,
                'render_probe_receipt_mismatch')
        info=dict(width=decoded.width,height=decoded.height,fps_numerator=decoded.fps.numerator,fps_denominator=decoded.fps.denominator,
            frames=decoded.frames_count,duration_seconds=float(duration),codec=decoded.codec,pixel_format=decoded.pixel_format,
            audio_streams=decoded.audio_streams,qa_state='REVIEW_REQUIRED',release_authorized=False,product_accepted=False,
            decoder_tools_sha256=decoded.tools_digest,execution_kind=receipt.execution_kind,composition_id=receipt.composition_id,
            input_sha256=receipt.input_sha256,recipe_sha256=receipt.recipe_sha256)
        return self._publish(p,run_id,'render',info,{'movie.mp4':data},origin,source_hash)

    def publish_game(self,p,run_id,ctx,bundle,manifest,files,*,source_hash,evidence_origin):
        self.s.authorize(p,'publish')
        require(evidence_origin in ('NATIVE_PRODUCER','SYNTHETIC_TEST'),'invalid_evidence_origin',400)
        require(type(manifest) is RuntimePackageManifest and type(files) is dict and 1<=len(files)<=MAX_FILES,
                'game_package_required',400)
        require(sum(len(v) for v in files.values() if type(v) is bytes)<=MAX_GAME_BYTES,'game_package_limit',413)
        try:
            verify_compiler_binding(ctx,bundle);manifest.validate()
            require(manifest.schema_version=='bie.game.runtime-package/2' and manifest.entrypoint=='runtime/index.html'
                and manifest.compiler_receipt_id==bundle.receipt.receipt_id
                and manifest.compiler_bundle_fingerprint==bundle.receipt.bundle_fingerprint,'game_compiler_binding_invalid')
            expected=fingerprint(dict(compiler_receipt_id=manifest.compiler_receipt_id,
                compiler_bundle_fingerprint=manifest.compiler_bundle_fingerprint,toolchain_fingerprint=manifest.toolchain_fingerprint,
                artifacts=[(a.path,a.sha256,a.size_bytes) for a in manifest.artifacts],entrypoint=manifest.entrypoint,
                asset_bindings=list(manifest.asset_bindings)))
            require(expected==manifest.package_fingerprint,'game_package_fingerprint_invalid')
            require(set(files)=={a.path for a in manifest.artifacts}|{'build-manifest.json'},'game_inventory_invalid')
            with TemporaryDirectory(prefix='bie-preview-validation-',dir=self.s.root) as root:
                root=Path(root)
                for path,data in files.items():
                    safe_relative(path)
                    require(all(not part.endswith((' ','.')) and not re.fullmatch(r'(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?',part,re.I)
                        for part in path.split('/')),'game_path_invalid')
                    require(type(data) is bytes and 0<len(data)<=MAX_FILE_BYTES,'game_file_limit',413)
                    require(Path(path).suffix in MIME,'game_media_type_invalid')
                    target=private_path(root,*path.split('/'));target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
                verify_package(root,manifest);verify_module_graph(root/'runtime')
                parser=ClosedHtml(files);parser.feed(files[manifest.entrypoint].decode('utf-8'))
                require(parser.scripts==['./entry.js'],'game_entry_script_missing')
                asset_map={ref:'../'+path for ref,path,_ in manifest.asset_bindings}
                require(files.get('runtime/entry.js')==ENTRY_JS.replace('__ASSET_BINDINGS__',json.dumps(asset_map,sort_keys=True,separators=(',',':'))).encode(),
                        'game_entry_not_canonical')
                for ref,path,digest_value in manifest.asset_bindings:
                    require(path in files and sha(files[path])==digest_value and ref in ctx.assets
                        and ctx.assets[ref].content_sha256==digest_value,'game_asset_binding_invalid')
        except OperatorError:raise
        except (ValueError,TypeError,KeyError,UnicodeError,OSError):raise OperatorError('game_package_invalid') from None
        # A signed sandbox/browser witness is a separate gate. A hash-sealed native
        # package is previewable, never sufficient evidence of pedagogic acceptance.
        info=dict(entrypoint=manifest.entrypoint,package_fingerprint=manifest.package_fingerprint,
            compiler_bundle_fingerprint=manifest.compiler_bundle_fingerprint,toolchain_fingerprint=manifest.toolchain_fingerprint,
            file_count=len(files),qa_state='REVIEW_REQUIRED',native_browser_acceptance='NOT_ATTESTED',
            release_authorized=False,product_accepted=False,compiled_package=True,playable_acceptance_claimed=False)
        return self._publish(p,run_id,'game',info,files,evidence_origin,source_hash)

    def _read(self,db,body,native,kind):
        require(kind in ('render','game'),'preview_kind_unavailable',404)
        bound=db.execute('SELECT * FROM graphs WHERE run=? AND kind=?',(body['run_id'],'artifact:preview:'+kind)).fetchone()
        if bound is None:return dict(kind=kind,status='NOT_RUN',reason='native_output_not_bound',product_accepted=False),{}
        records=self.art.inventory(db,body,native);r=records[bound['artifact']];api=self.art.canonical_api(records,native)
        require(r.artifact_type=='operator.preview.'+kind,'preview_binding_invalid')
        envelope=strict_json(api.content(r.artifact_id),256*1024)
        require(type(envelope) is dict and set(envelope)=={'schema','kind','source_hash','origin','info','files','artifact_ids'}
            and envelope['schema']=='bie.operator.preview/1' and envelope['kind']==kind and envelope['source_hash']==body['source_hash']
            and envelope['origin'] in ('NATIVE_PRODUCER','SYNTHETIC_TEST'),'preview_manifest_invalid')
        rows=envelope['files'];ids=envelope['artifact_ids']
        require(type(rows) is dict and 1<=len(rows)<=MAX_FILES and type(ids) is dict and set(rows)==set(ids),'preview_inventory_invalid')
        data={}
        for path,v in rows.items():
            aid=ids[path];require(aid in r.parent_artifact_ids and aid in records,'preview_parent_invalid')
            rec=records[aid];require(rec.artifact_type=='operator.preview.file' and v==dict(sha256=rec.blob_digest,size_bytes=rec.blob_size),
                                   'preview_file_binding_invalid')
            data[path]=api.content(aid)
        require(sum(map(len,data.values()))<=MAX_BLOB,'preview_package_limit',413)
        for ref in r.parent_artifact_ids:api.content(ref)
        return dict(kind=kind,status='AVAILABLE',artifact_id=r.artifact_id,sha256=r.blob_digest,
            source_hash=body['source_hash'],origin=envelope['origin'],fixture_evidence=envelope['origin']=='SYNTHETIC_TEST',
            info=envelope['info'],integrity='VERIFIED',product_accepted=False),data

    def get(self,p,run_id,kind):
        with self.art.context(p,run_id) as args:return self._read(*args,kind)[0]

    def media(self,p,run_id,value=None,if_range=None):
        with self.art.context(p,run_id) as args:
            meta,data=self._read(*args,'render');require(meta['status']=='AVAILABLE','render_not_found',404)
            raw=data['movie.mp4'];etag='"'+sha(raw)+'"';a,b,status=byte_range(value,len(raw),etag,if_range)
            headers={'Accept-Ranges':'bytes','ETag':etag,'Content-Length':str(b-a+1)}
            if status==206:headers['Content-Range']=f'bytes {a}-{b}/{len(raw)}'
            return raw[a:b+1],status,headers

    def grant(self,p,run_id,credential,ttl=120):
        require(type(ttl) is int and 1<=ttl<=300,'preview_grant_ttl_invalid',400)
        binding=self.s.credentials.access_binding(credential,p)
        meta=self.get(p,run_id,'game');require(meta['status']=='AVAILABLE','game_not_found',404)
        with self._lock:
            now=self.clock();self._grants={k:v for k,v in self._grants.items() if v['until']>now}
            require(len(self._grants)<MAX_GRANTS,'preview_grant_limit',429)
            ticket=secrets.token_urlsafe(32)
            self._grants[ticket]=dict(principal=p,binding=binding,run=run_id,until=now+ttl,manifest=meta['sha256'])
        return dict(preview_path='/_preview/'+ticket+'/runtime/index.html',expires_in_seconds=ttl,
                    sandbox='allow-scripts',product_accepted=False)

    def revoke(self,p):
        self.s.authorize(p,'read')
        with self._lock:self._grants={k:v for k,v in self._grants.items() if v['principal']!=p}

    def game_file(self,ticket,path):
        require(type(ticket) is str and re.fullmatch(r'[A-Za-z0-9_-]{43}',ticket) is not None,'preview_not_found',404)
        with self._lock:grant=self._grants.get(ticket)
        require(grant is not None and grant['until']>self.clock(),'preview_expired_or_revoked',401)
        self.s.credentials.check_binding(grant['binding'],grant['principal'],'read')
        try:safe_relative(path)
        except ValueError:raise OperatorError('preview_not_found',404) from None
        require(path!='build-manifest.json' and Path(path).suffix in MIME,'preview_not_found',404)
        with self.art.context(grant['principal'],grant['run']) as args:
            meta,data=self._read(*args,'game')
            require(meta['status']=='AVAILABLE' and meta['sha256']==grant['manifest'],'preview_manifest_changed')
            require(path in data,'preview_not_found',404)
            # Original artifact bytes remain unchanged. Remove only the native
            # meta CSP: the HTTP sandbox/CSP below is authoritative and stricter.
            raw=data[path]
            if Path(path).suffix=='.html':
                raw=re.sub(rb'<meta http-equiv="Content-Security-Policy" content="[^"]*">',b'',raw)
            with self._lock:require(self._grants.get(ticket) is grant and grant['until']>self.clock(),'preview_expired_or_revoked',401)
            self.s.credentials.check_binding(grant['binding'],grant['principal'],'read')
            return raw,MIME[Path(path).suffix]
