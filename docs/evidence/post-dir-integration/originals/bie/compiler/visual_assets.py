"""H11 verified visual-asset handoff on the existing ASSET -> COMP path.

No download or ambient paths. Decoders execute through the kernel-isolated H7
worker, not in the source compiler. Rights/provenance references are retained
assertions, not independent licensing or educational approval.
"""
from __future__ import annotations
from copy import deepcopy
from dataclasses import asdict
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import json, os, re, stat, sys, tempfile
from .qa_common import CompilerQAError, digest
from .linux_worker import WorkerPolicy, run_isolated
from .installed_toolchain import file_hash

SCHEMA = 'bie.comp-visual-assets.v1'
KEY = 'compiler_media_v1'
MAX_FILE = 64 * 1024**2
MAX_TOTAL = 256 * 1024**2
TYPES = {'image/png': ('image', 'png'), 'image/jpeg': ('image', 'jpg'),
         'image/webp': ('image', 'webp'), 'video/mp4': ('video', 'mp4')}
FIELDS = {'asset_id', 'public_path', 'sha256', 'byte_length', 'media_type',
          'media', 'rights_ref', 'source_refs', 'reasoning_refs'}

def fail(code, message=''):
    raise CompilerQAError(code + (': ' + str(message) if message else ''))

def integer(value, lo, hi, code):
    if type(value) is not int or not lo <= value <= hi:
        fail(code)
    return value

def references(value):
    if not isinstance(value, list) or not value or len(value) > 128 or any(not isinstance(x,str) or not x.strip() or len(x)>2048 for x in value) or len(set(value)) != len(value):
        fail('MEDIA_PROVENANCE_REQUIRED')
    return value

def validate_descriptor(row):
    if not isinstance(row, dict) or set(row) != FIELDS:
        fail('MEDIA_DESCRIPTOR_FIELDS')
    for key in ('asset_id', 'rights_ref'):
        if not isinstance(row[key], str) or not row[key].strip() or len(row[key]) > 2048:
            fail('MEDIA_IDENTITY_OR_RIGHTS_REQUIRED')
    h=row['sha256']
    if not isinstance(h,str) or not re.fullmatch('[0-9a-f]{64}',h):fail('MEDIA_SHA256_INVALID')
    integer(row['byte_length'],1,MAX_FILE,'MEDIA_BYTE_BUDGET')
    if row['media_type'] not in TYPES:fail('MEDIA_TYPE_UNSUPPORTED')
    kind, ext=TYPES[row['media_type']]
    # Both original ASSET bundler (20 chars) and full content-addressed paths.
    extensions = {ext,'jpeg'} if ext=='jpg' else {ext}
    if row['public_path'] not in {'assets/'+prefix+'.'+suffix for prefix in (h,h[:20]) for suffix in extensions}:
        fail('MEDIA_CONTENT_PATH_INVALID')
    references(row['source_refs']);references(row['reasoning_refs'])
    m=row['media']
    base={'kind','width','height','frame_count'}
    extra={'format'} if kind=='image' else {'codec','pixel_format','fps_num','fps_den','audio_streams'}
    if not isinstance(m,dict) or set(m)!=base|extra or m.get('kind')!=kind:fail('MEDIA_METADATA_FIELDS')
    integer(m['width'],1,16384,'MEDIA_DIMENSIONS');integer(m['height'],1,16384,'MEDIA_DIMENSIONS')
    if m['width']*m['height']>16_000_000:fail('MEDIA_PIXEL_BUDGET')
    integer(m['frame_count'],1,36000,'MEDIA_FRAME_BUDGET')
    if kind=='image':
        if m['frame_count']!=1 or m['format']!={'png':'png','jpg':'jpeg','webp':'webp'}[ext]:fail('MEDIA_IMAGE_METADATA')
    else:
        if m['codec']!='h264' or m['pixel_format']!='yuv420p':fail('MEDIA_VIDEO_PROFILE_UNSUPPORTED')
        integer(m['fps_num'],1,240000,'MEDIA_FPS');integer(m['fps_den'],1,10000,'MEDIA_FPS')
        if not Fraction(1) <= Fraction(m['fps_num'],m['fps_den']) <= Fraction(240):fail('MEDIA_FPS')
        integer(m['audio_streams'],0,1,'MEDIA_AUDIO_PROFILE')
    return row

def plan_visual_assets(raw, *, required=True):
    elements=[e for e in raw.get('elements',[]) if e['element_type'] in {'image','video'}]
    cfg=raw.get('metadata',{}).get(KEY)
    if cfg is None:
        if elements and required:fail('MEDIA_ASSET_MANIFEST_REQUIRED','use the existing bundle-to-scene binding adapter')
        return None
    if not isinstance(cfg,dict) or set(cfg)!={'schema_version','assets'} or cfg['schema_version']!=SCHEMA:
        fail('MEDIA_MANIFEST_VERSION_OR_FIELDS')
    assets=cfg['assets']
    if not isinstance(assets,list) or not 1<=len(assets)<=64:fail('MEDIA_ASSET_COUNT')
    byid={};paths={}
    for row in assets:
        validate_descriptor(row)
        if row['asset_id'] in byid:fail('MEDIA_DUPLICATE_ASSET')
        if row['public_path'] in paths and paths[row['public_path']]!=row['sha256']:fail('MEDIA_PATH_COLLISION')
        paths[row['public_path']]=row['sha256'];byid[row['asset_id']]=row
    if sum(x['byte_length'] for x in assets)>MAX_TOTAL:fail('MEDIA_TOTAL_BYTE_BUDGET')
    used=set();bindings=[]
    for e in elements:
        props=e['props'];aid=props.get('asset_ref')
        if not isinstance(aid,str):fail('MEDIA_ASSET_REFERENCE_REQUIRED')
        aid=aid.removeprefix('asset://')
        if aid not in byid:fail('MEDIA_UNRESOLVED_ASSET',e['element_id'])
        row=byid[aid]
        if props.get('resolved_asset_path')!=row['public_path']:fail('MEDIA_RESOLVED_PATH_MISMATCH')
        if row['media']['kind']!=e['element_type']:fail('MEDIA_KIND_MISMATCH')
        if props.get('rights_ref')!=row['rights_ref']:fail('MEDIA_RIGHTS_REFERENCE_MISMATCH')
        if not set(row['source_refs'])<=set(e['source_refs']) or not set(row['reasoning_refs'])<=set(e['reasoning_refs']):fail('MEDIA_PROVENANCE_UNBOUND')
        used.add(aid);bindings.append({'element_id':e['element_id'],'asset_id':aid})
    if used!=set(byid):fail('MEDIA_UNUSED_ASSET')
    plan={'schema_version':SCHEMA,'assets':sorted(deepcopy(assets),key=lambda r:r['asset_id']),
          'bindings':sorted(bindings,key=lambda r:r['element_id']),'accepted':False}
    plan['plan_sha256']=digest(plan)
    return plan

def read_visual_file(root, relative, maximum):
    root=Path(root).absolute()
    if root.is_symlink() or not root.is_dir() or any(p.is_symlink() for p in root.parents):fail('MEDIA_ASSET_ROOT_INVALID')
    if not isinstance(relative,str) or not re.fullmatch(r'assets/[0-9a-f]{20}(?:[0-9a-f]{44})?\.(?:png|jpg|jpeg|webp|mp4)',relative):fail('MEDIA_CONTENT_PATH_INVALID')
    fd=None
    try:
        fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
        child=os.open('assets',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=fd);os.close(fd);fd=child
        f=os.open(relative.split('/')[1],os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=fd)
        try:
            before=os.fstat(f)
            if not stat.S_ISREG(before.st_mode) or not 1<=before.st_size<=maximum:fail('MEDIA_FILE_TYPE_OR_SIZE')
            chunks=[];count=0
            while True:
                part=os.read(f,min(65536,maximum+1-count))
                if not part:break
                count+=len(part);chunks.append(part)
                if count>maximum:fail('MEDIA_FILE_GREW')
            after=os.fstat(f)
            if (before.st_size,before.st_mtime_ns,before.st_ctime_ns)!=(after.st_size,after.st_mtime_ns,after.st_ctime_ns):fail('MEDIA_FILE_CHANGED')
            return b''.join(chunks)
        finally:os.close(f)
    except OSError as exc:fail('MEDIA_ASSET_UNAVAILABLE',exc)
    finally:
        if fd is not None:os.close(fd)

def _video_metadata(streams, frames):
    video=[s for s in streams if s.get('codec_type')=='video'];audio=[s for s in streams if s.get('codec_type')=='audio']
    if len(video)!=1 or len(audio)>1 or len(video)+len(audio)!=len(streams):fail('MEDIA_VIDEO_STREAMS_UNSUPPORTED')
    s=video[0]
    if s.get('codec_name')!='h264' or s.get('pix_fmt')!='yuv420p' or s.get('sample_aspect_ratio','1:1') not in {'1:1','N/A'}:fail('MEDIA_VIDEO_PROFILE_UNSUPPORTED')
    if any(a.get('codec_name')!='aac' or a.get('channels') not in (1,2) for a in audio):fail('MEDIA_AUDIO_PROFILE')
    if s.get('tags',{}).get('rotate','0')!='0' or any(x.get('rotation',0)!=0 for x in s.get('side_data_list',[])):fail('MEDIA_VIDEO_ROTATION_UNSUPPORTED')
    try:
        fps=Fraction(s['avg_frame_rate']);tb=Fraction(s['time_base']);n=len(frames)
        if not 1<=n<=36000 or not 1<=fps<=240 or Fraction(s['r_frame_rate'])!=fps:fail('MEDIA_CFR_REQUIRED')
        stamps=[int(f['best_effort_timestamp']) for f in frames]
        if any(Fraction(ts)*tb != Fraction(i,1)/fps for i,ts in enumerate(stamps)):fail('MEDIA_CFR_ZERO_ORIGIN_REQUIRED')
        if 'nb_frames' in s and int(s['nb_frames'])!=n:fail('MEDIA_VIDEO_FRAME_COUNT_MISMATCH')
        if Fraction(int(s['duration_ts']))*tb != Fraction(n,1)/fps:fail('MEDIA_VIDEO_DURATION_MISMATCH')
    except (KeyError,ValueError,ZeroDivisionError,TypeError) as exc:
        if isinstance(exc,CompilerQAError):raise
        fail('MEDIA_VIDEO_TIMESTAMP_METADATA',exc)
    return {'kind':'video','width':s['width'],'height':s['height'],'codec':'h264','pixel_format':'yuv420p',
            'frame_count':n,'fps_num':fps.numerator,'fps_den':fps.denominator,'audio_streams':len(audio)}

def inspect_visual_bytes(data, media_type):
    if not isinstance(data,bytes) or not 1<=len(data)<=MAX_FILE:fail('MEDIA_BYTE_BUDGET')
    if media_type not in TYPES:fail('MEDIA_TYPE_UNSUPPORTED')
    kind,ext=TYPES[media_type];executions=[]
    root_engine=Path(__file__).resolve().parents[3]
    policy=WorkerPolicy(procfs=False,cpu_seconds=60,file_bytes=MAX_FILE,address_space_bytes=2*1024**3)
    with tempfile.TemporaryDirectory(prefix='bie-media-verify-') as td:
        root=Path(td);path=root/('input.'+ext);path.write_bytes(data)
        def run(command, maximum=8*1024**2):
            p,k=run_isolated(command,workspace=root,engine=root_engine,policy=policy,timeout_s=65,max_output_bytes=maximum)
            executions.append({'process':asdict(p),'kernel_policy':k})
            if not p.process.passed:fail('MEDIA_DECODE_BLOCKED',p.outcome+':'+p.process.stderr[:1000])
            try:return json.loads(p.process.stdout)
            except ValueError:fail('MEDIA_DECODER_OUTPUT_INVALID')
        if kind=='image':
            info=run([sys.executable,'-I',str(Path(__file__).with_name('visual_asset_worker.py')),str(path)])
            tools={'python':file_hash(Path(sys.executable).resolve())[0],'worker':file_hash(Path(__file__).with_name('visual_asset_worker.py'))[0]}
        else:
            tool='/usr/bin/ffprobe';tool_hash=file_hash(Path(tool).resolve())[0]
            meta=run([tool,'-v','error','-protocol_whitelist','file','-show_streams','-of','json',str(path)])
            frame_data=run([tool,'-v','error','-protocol_whitelist','file','-select_streams','v:0','-show_frames','-show_entries','frame=best_effort_timestamp','-of','json',str(path)])
            info=_video_metadata(meta.get('streams',[]),frame_data.get('frames',[]));tools={'ffprobe':tool_hash}
            if file_hash(Path(tool).resolve())[0]!=tool_hash:fail('MEDIA_DECODER_CHANGED')
    if info['kind']=='image' and info['format']!={'png':'png','jpg':'jpeg','webp':'webp'}[ext]:fail('MEDIA_MIME_BYTES_MISMATCH')
    return info,{'schema_version':'bie.visual-byte-inspection.v1','sha256':sha256(data).hexdigest(),
                 'byte_length':len(data),'media':info,'tools':tools,'executions':executions,
                 'kernel_isolated':all(e['kernel_policy'].get('kernel_enforced') is True for e in executions),'accepted':False}

def verified_visual_bytes(raw, asset_root):
    plan=plan_visual_assets(raw)
    if plan is None:return {},{'schema_version':'bie.verified-visual-assets.v1','status':'NOT_REQUIRED','assets':[],'accepted':False}
    if asset_root is None:fail('MEDIA_ASSET_ROOT_REQUIRED')
    data_by_path={};records=[];cache={}
    for row in plan['assets']:
        data=read_visual_file(asset_root,row['public_path'],row['byte_length'])
        if len(data)!=row['byte_length'] or sha256(data).hexdigest()!=row['sha256']:fail('MEDIA_ASSET_HASH_MISMATCH',row['asset_id'])
        key=(row['sha256'],row['media_type'])
        if key not in cache:cache[key]=inspect_visual_bytes(data,row['media_type'])
        info,proof=cache[key]
        if info!=row['media']:fail('MEDIA_ASSET_METADATA_MISMATCH',row['asset_id'])
        data_by_path[row['public_path']]=data
        # Stable semantic receipt, not nondeterministic child-process timings.
        records.append({**deepcopy(row),'decoder_identity':proof['tools'],'kernel_isolated':proof['kernel_isolated']})
    return data_by_path,{'schema_version':'bie.verified-visual-assets.v1','status':'BYTES_AND_BOUNDED_METADATA_VERIFIED',
                         'plan_sha256':plan['plan_sha256'],'assets':records,'accepted':False}

def bind_visual_bundle(payload, bundle_receipt, asset_root):
    """Adopt original bundle_assets receipts; do not trust their `passed` alone.

    Returns a new Scene IR and binding evidence. Existing source/rights fields,
    crop/trim intent, and all nonasset scene data are preserved. Actual bytes
    are read and decoded before constructing the versioned manifest.
    """
    from .asset_path_resolver import CompilerAssetPathRegistry
    if not bundle_receipt.passed or bundle_receipt.blockers:fail('MEDIA_BUNDLE_BLOCKED')
    raw=deepcopy(payload)
    if KEY in raw.get('metadata',{}):fail('MEDIA_ALREADY_BOUND')
    registry=CompilerAssetPathRegistry();records={}
    for r in bundle_receipt.bundled:
        registry.register(r);records[r.asset_id]=r
    used={};bindings=[]
    for e in raw.get('elements',[]):
        if e['element_type'] not in {'image','video'}:continue
        props=e['props'];resolved=registry.require(props.get('asset_ref'));r=records[resolved.asset_id]
        if props.get('rights_ref')!=r.rights_basis:fail('MEDIA_RIGHTS_REFERENCE_MISMATCH')
        if props.get('resolved_asset_path',resolved.resolved_public_path)!=resolved.resolved_public_path:fail('MEDIA_PREBOUND_PATH_MISMATCH')
        data=read_visual_file(asset_root,resolved.resolved_public_path,MAX_FILE)
        if sha256(data).hexdigest()!=r.sha256:fail('MEDIA_ASSET_HASH_MISMATCH')
        info,_=inspect_visual_bytes(data,r.media_type)
        d={'asset_id':r.asset_id,'public_path':r.public_path,'sha256':r.sha256,'byte_length':len(data),'media_type':r.media_type,
           'media':info,'rights_ref':r.rights_basis,'source_refs':e['source_refs'][:],'reasoning_refs':e['reasoning_refs'][:]}
        validate_descriptor(d)
        if r.asset_id in used and used[r.asset_id]!=d:fail('MEDIA_SHARED_ASSET_PROVENANCE_MISMATCH')
        used[r.asset_id]=d;props['resolved_asset_path']=r.public_path;bindings.append(e['element_id'])
    if not used:fail('MEDIA_NO_VISUAL_ASSETS')
    raw.setdefault('metadata',{})[KEY]={'schema_version':SCHEMA,'assets':sorted(used.values(),key=lambda x:x['asset_id'])}
    plan_visual_assets(raw)
    return raw,{'schema_version':'bie.visual-bundle-binding.v1','original_document_sha256':digest(payload),
               'bound_document_sha256':digest(raw),'bound_elements':bindings,'accepted':False,
               'rights_status':'SUPPLIED_REFERENCE_NOT_INDEPENDENT_PERMISSION_VERIFICATION'}
