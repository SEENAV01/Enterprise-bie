"""Actual local compile / media / output-byte collectors.

These routines are for evaluator-controlled local workers. They do NOT provide
multi-tenant process isolation or authenticated evidence custody. No candidate
shell commands, compiler plugins, external URLs, or candidate code execution.
"""
from __future__ import annotations
import base64, hashlib, json, os, platform, shutil, subprocess, sys, tempfile
from fractions import Fraction
from pathlib import Path, PurePosixPath
from ..models import BenchmarkError,digest,digest_string,ident,text
from ..domains.structured import sequence
from .delivery_common import integer,seal

def sha(data):return hashlib.sha256(data).hexdigest()

def safe_relative(name):
    if type(name) is not str or not name or '\\' in name or ':' in name or '\x00' in name:
        raise BenchmarkError('UNSAFE_OUTPUT_PATH')
    p=PurePosixPath(name)
    if p.is_absolute() or any(x in ('','.','..') for x in name.split('/')):
        raise BenchmarkError('UNSAFE_OUTPUT_PATH')
    return name

def local_bytes(path,maximum=20000000):
    p=Path(path)
    if any(v.is_symlink() for v in [p,*p.parents]) or not p.is_file():
        raise BenchmarkError('ARTIFACT_NOT_REGULAR_FILE')
    if p.stat().st_size>maximum:raise BenchmarkError('ARTIFACT_SIZE_LIMIT')
    data=p.read_bytes()
    if len(data)>maximum:raise BenchmarkError('ARTIFACT_SIZE_LIMIT')
    return data

def tool(name):
    value=shutil.which(name)
    if not value:raise BenchmarkError('LOCAL_TOOL_UNAVAILABLE',name)
    return str(Path(value).resolve())

def command(argv,cwd,timeout=20):
    # Drop PYTHONPATH, NODE_OPTIONS, compiler config and FFREPORT injections.
    env={'PATH':os.environ.get('PATH','/usr/bin:/bin'),'HOME':str(cwd),'LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC'}
    with tempfile.TemporaryFile() as out,tempfile.TemporaryFile() as err:
        try:
            p=subprocess.run(argv,cwd=cwd,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=err,
                             timeout=timeout,check=False,shell=False)
        except subprocess.TimeoutExpired as exc:raise BenchmarkError('LOCAL_TOOL_TIMEOUT') from exc
        out.seek(0);err.seek(0);o=out.read(1000001);e=err.read(1000001)
        if len(o)>1000000 or len(e)>1000000:raise BenchmarkError('LOCAL_TOOL_OUTPUT_LIMIT')
    return p.returncode,o,e

def publish(root,files,receipt):
    if root is None:return
    root=Path(root);root.mkdir(parents=True,exist_ok=False)
    for name,data in files.items():
        safe_relative(name);p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    (root/'COLLECTOR_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')

def compile_source(language: str,source: str,run_id: str,output_dir: str | Path | None = None) -> dict:
    """Compile a bounded UTF-8 source without executing its top-level code.

    Python emits checked-hash pyc; TypeScript emits JS with noEmitOnError. This
    does not bundle Remotion, resolve project imports, or prove runtime behavior.
    """
    if type(language) is not str or language not in {'python','typescript'}:raise BenchmarkError('UNSUPPORTED_COMPILER_PROFILE')
    text(source,maximum=50000);ident(run_id);data=source.encode('utf-8')
    with tempfile.TemporaryDirectory(prefix='bie-compile-') as d:
        root=Path(d);files={}
        if language=='python':
            name='lesson.py';(root/name).write_bytes(data)
            snippet=('import py_compile; py_compile.compile("lesson.py",cfile="lesson.pyc",'
                     'dfile="lesson.py",doraise=True,optimize=0,'
                     'invalidation_mode=py_compile.PycInvalidationMode.CHECKED_HASH)')
            argv=[sys.executable,'-I','-S','-c',snippet]
            version=platform.python_version();output_name='lesson.pyc';profile='python-checked-hash-bytecode-v1'
        else:
            name='lesson.ts';(root/name).write_bytes(data)
            exe=tool('tsc');rc,vo,ve=command([exe,'--version'],root)
            if rc:raise BenchmarkError('COMPILER_VERSION_PROBE_FAILED')
            version=vo.decode('utf-8').strip();output_name='lesson.js';profile='typescript-strict-emit-v1'
            argv=[exe,'lesson.ts','--strict','--noEmitOnError','--target','ES2020','--module','commonjs',
                  '--skipLibCheck','--pretty','false','--outDir','out']
        rc,out,err=command(argv,root)
        p=root/(output_name if language=='python' else 'out/'+output_name)
        emitted=p.read_bytes() if p.is_file() else b''
        facts={'language':language,'command_profile':profile,'compiler_version':version,'exit_code':rc,
               'source_bytes':len(data),'output_bytes':len(emitted),'output_sha256':sha(emitted),
               'stdout_sha256':sha(out),'stderr_sha256':sha(err)}
        receipt=seal('compile',run_id,sha(data),facts)
        files={'source/'+name:data,'stdout.txt':out,'stderr.txt':err,
               'COMMAND.json':json.dumps({'argv':argv,'shell':False,'candidate_executed':False},indent=2).encode()}
        if emitted:files['output/'+output_name]=emitted
        publish(output_dir,files,receipt)
        return receipt

def decode_media(path: str | Path,run_id: str,frame_indices=(0,),output_dir: str | Path | None = None) -> tuple[dict,dict]:
    """Freeze file bytes, probe and fully decode one bounded video stream.

    Maximum 20MB file, 320x180, 300frames, 20s. Sample RGB evidence is capped at
    240k raw bytes. Audio presence is inventoried; audio content is NOT decoded.
    No hardware decoding or external/network protocols are enabled.
    """
    ident(run_id);data=local_bytes(path)
    if not data:raise BenchmarkError('EMPTY_MEDIA_ARTIFACT')
    if type(frame_indices) not in (list,tuple):raise BenchmarkError('INVALID_FRAME_REQUEST')
    indices=[integer(v,0,299) for v in sequence(list(frame_indices),lower=1,upper=8)]
    if len(set(indices))!=len(indices):raise BenchmarkError('DUPLICATE_FRAME_REQUEST')
    with tempfile.TemporaryDirectory(prefix='bie-media-') as d:
        root=Path(d);f=root/'input.media';f.write_bytes(data)
        probe=tool('ffprobe');ffmpeg=tool('ffmpeg')
        args=[probe,'-v','error','-protocol_whitelist','file,pipe','-format_whitelist','matroska,webm,mov',
              '-show_streams','-show_format','-show_frames','-show_entries',
              'stream=index,codec_type,codec_name,width,height,avg_frame_rate:format=duration:frame=media_type,width,height,best_effort_timestamp_time',
              '-of','json',str(f)]
        rc,raw,err=command(args,root)
        if rc or err:raise BenchmarkError('MEDIA_PROBE_FAILED')
        try:
            p=json.loads(raw);vs=[s for s in p['streams'] if s['codec_type']=='video'];audio=[s for s in p['streams'] if s['codec_type']=='audio']
            if len(vs)!=1:raise BenchmarkError('SINGLE_VIDEO_STREAM_REQUIRED')
            v=vs[0];w=integer(v['width'],1,320);h=integer(v['height'],1,180)
            fps=Fraction(v['avg_frame_rate']);duration=Fraction(p['format']['duration'])
            if not 0<fps<=120 or not 0<duration<=20:raise BenchmarkError('MEDIA_PROFILE_LIMIT')
            frames=[x for x in p['frames'] if x['media_type']=='video']
            if not 1<=len(frames)<=300:raise BenchmarkError('MEDIA_FRAME_LIMIT')
            if any((x['width'],x['height'])!=(w,h) for x in frames):raise BenchmarkError('VARIABLE_FRAME_DIMENSIONS')
            pts=[Fraction(x['best_effort_timestamp_time']) for x in frames]
        except (KeyError,TypeError,ValueError,ZeroDivisionError) as exc:raise BenchmarkError('INVALID_MEDIA_METADATA') from exc
        if any(a>=b for a,b in zip(pts,pts[1:])):raise BenchmarkError('NONMONOTONIC_MEDIA_TIMESTAMPS')
        if any(i>=len(frames) for i in indices):raise BenchmarkError('REQUESTED_FRAME_NOT_DECODED')
        if len(indices)*w*h*3>240000:raise BenchmarkError('FRAME_EVIDENCE_SIZE_LIMIT')
        argv=[ffmpeg,'-nostdin','-v','error','-xerror','-threads','1','-protocol_whitelist','file,pipe',
              '-format_whitelist','matroska,webm,mov','-i',str(f),'-map','0:v:0','-an','-sn','-dn',
              '-fps_mode','passthrough','-frames:v','301','-pix_fmt','rgb24','-f','rawvideo','decoded.rgb']
        rc,out,decode_err=command(argv,root,30)
        if rc or decode_err:raise BenchmarkError('MEDIA_DECODE_FAILED')
        rgb=local_bytes(root/'decoded.rgb',maximum=52000000);stride=w*h*3
        if len(rgb)!=len(frames)*stride:raise BenchmarkError('DECODED_BYTE_COUNT_MISMATCH')
        rc,ver,e=command([ffmpeg,'-version'],root)
        if rc:raise BenchmarkError('MEDIA_TOOL_VERSION_FAILED')
        hashes=[sha(rgb[i*stride:(i+1)*stride]) for i in range(len(frames))]
        facts={'width':w,'height':h,'fps':str(fps),'container_duration':str(duration),
               'decoded_frames':len(frames),'video_streams':len(vs),'audio_streams':len(audio),
               'pts_seconds':[str(x) for x in pts],'frame_sha256':hashes,'decoded_sha256':sha(rgb),
               'decoder_version':ver.decode().splitlines()[0],'decode_exit_code':0,'codec':v['codec_name']}
        render=seal('media',run_id,sha(data),facts)
        samples=[]
        for i in sorted(indices):
            b=rgb[i*stride:(i+1)*stride]
            samples.append({'id':'frame:'+str(i),'index':i,'width':w,'height':h,
                            'rgb_base64':base64.b64encode(b).decode(),'raw_sha256':sha(b)})
        frame_receipt=seal('frames',run_id,sha(data),{'frames':samples,'total_frame_count':len(frames)})
        publish(output_dir,{'input.media':data,'probe.json':raw,'probe_stderr.txt':err,'decode_stderr.txt':decode_err,
                            'decoded.rgb':rgb,'FRAME_RECEIPT.json':json.dumps(frame_receipt,indent=2).encode(),
                            'COMMANDS.json':json.dumps([args,argv],indent=2).encode()},render)
        return render,frame_receipt

def snapshot_outputs(root,run_id,inputs_sha256,recipe_sha256,environment_sha256,seed):
    """Hash actual output bytes, rejecting symlinks and ambiguous paths.

    Call AFTER a build in a new evaluator-owned directory. Hashing a directory
    alone does not prove how its contents were built; preserve execution logs.
    """
    ident(run_id);integer(seed,0,2**32-1)
    for v in [inputs_sha256,recipe_sha256,environment_sha256]:digest_string(v)
    root=Path(root)
    if any(v.is_symlink() for v in [root,*root.parents]) or not root.is_dir():raise BenchmarkError('OUTPUT_ROOT_NOT_DIRECTORY')
    records=[];seen=set();total=0
    for p in sorted(root.rglob('*')):
        if p.is_symlink():raise BenchmarkError('OUTPUT_SYMLINK_FORBIDDEN')
        if p.is_dir():continue
        name=safe_relative(p.relative_to(root).as_posix())
        if name.casefold() in seen:raise BenchmarkError('CASE_COLLIDING_OUTPUT_PATHS')
        seen.add(name.casefold());data=local_bytes(p,20000000);total+=len(data)
        if total>50000000 or len(records)>=128:raise BenchmarkError('OUTPUT_SNAPSHOT_LIMIT')
        records.append({'path':name,'bytes':len(data),'sha256':sha(data)})
    if not records:raise BenchmarkError('EMPTY_OUTPUT_SNAPSHOT')
    facts={'workspace_sha256':sha(str(root.resolve()).encode()),'inputs_sha256':inputs_sha256,
           'recipe_sha256':recipe_sha256,'environment_sha256':environment_sha256,'seed':seed,'outputs':records}
    return seal('output-snapshot',run_id,digest(records),facts)
