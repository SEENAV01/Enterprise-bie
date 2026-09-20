"""H7 actual-render producer and process-bound QA witness.

Only a run started here can mint the in-process witness. JSON reports, hashes or
legacy browser-double receipts alone never authorize this gate. Pin validation
precedes execution. Dependency or Linux policy failure stops, without fallback.
"""
from __future__ import annotations
from dataclasses import asdict,dataclass,replace
from pathlib import Path
import json, secrets, shutil, tempfile
from .qa_common import CompilerQAError,digest
from .artifact_hashing import canonical_json
from .installed_toolchain import collect_installed_toolchain,require_same_toolchain,file_hash
from .linux_worker import run_isolated,WorkerPolicy
from .layout_measurements import inspect_owner_fit
from .content_fit_qa import DECLARED_SCOPE
from .paint_quality import inspect_paint_quality

_SEAL=object()
@dataclass(frozen=True)
class ActualPaintWitness:
    source_manifest_sha256:str
    evidence_sha256:str
    toolchain_sha256:str
    frame_count:int
    passed:bool
    evidence:dict
    _seal:object


def require_actual_witness(value,manifest):
    if not isinstance(value,ActualPaintWitness) or value._seal is not _SEAL or not value.passed or value.source_manifest_sha256!=manifest or digest(value.evidence)!=value.evidence_sha256:
        raise CompilerQAError('ACTUAL_PAINT_WITNESS_REQUIRED')
    return value


def capture_entry(request,measure_js,paint_js):
    """Original Scene.tsx and every component remain byte-identical."""
    return '''import React, {useMemo, useLayoutEffect} from "react";
import {Composition,registerRoot,useCurrentFrame,delayRender,continueRender,cancelRender} from "remotion";
import {Scene} from "./src/Scene";
const req = REQUEST as const;
const baseMeasure = MEASURE;
const paintMeasure = PAINT;
const Observer:React.FC = () => {
 const frame=useCurrentFrame();
 const handle=useMemo(()=>delayRender("bie-frame-paint-"+frame),[frame]);
 useLayoutEffect(()=>{let closed=false;
  (async()=>{
   await document.fonts.ready;
   await new Promise<void>(r=>requestAnimationFrame(()=>requestAnimationFrame(()=>r())));
   if(closed)return;
   const options={frame,equationFonts:req.equationFonts};
   console.info("BIE_PAINT_V1:"+JSON.stringify({nonce:req.nonce,frame,fonts_ready:document.fonts.status==="loaded",records:baseMeasure(options),paint_records:paintMeasure(options)}));
   continueRender(handle);closed=true;
  })().catch(e=>cancelRender(e));
  return ()=>{if(!closed){continueRender(handle);closed=true;}};
 },[frame,handle]);
 return null;
};
const MeasuredScene:React.FC = () => <><Scene/><Observer/></>;
const Root:React.FC = () => <Composition id={req.composition_id} component={MeasuredScene} width={req.width} height={req.height} fps={req.fps} durationInFrames={req.frame_count}/>;
registerRoot(Root);
'''.replace('const req = REQUEST as const;', 'const req = '+json.dumps(request,ensure_ascii=True)+' as const;').replace('const baseMeasure = MEASURE;', 'const baseMeasure = '+measure_js.strip()+';').replace('const paintMeasure = PAINT;', 'const paintMeasure = '+paint_js.strip()+';')


def isolated_typecheck(root, *, node, evidence_directory):
    from .generated_code_regression import typecheck_generated_workspace
    root=Path(root).resolve();rows=[]
    def execute(command,**kw):
        # tsc CLI can run without procfs. This explicit profile is NOT the browser profile.
        p,e=run_isolated([str(node),str(root/'node_modules/typescript/bin/tsc'),*list(command)[1:]],workspace=root,
                         policy=WorkerPolicy(procfs=False),timeout_s=kw.get('timeout_s',90),max_output_bytes=8*1024**2)
        rows.append({'process':asdict(p),'kernel_policy':e})
        return replace(p,process=replace(p.process,stdout=p.process.stdout.replace('/work/',str(root)+'/')))
    result=typecheck_generated_workspace(root,process_runner=execute)
    Path(evidence_directory).mkdir(parents=True,exist_ok=True)
    (Path(evidence_directory)/'TYPECHECK.json').write_bytes(canonical_json({'receipt':asdict(result),'executions':rows}))
    return result


def produce_actual_paint(workspace,output, *, node,browser,target,policy=None):
    from .hardened_scene_compile import require_h3_workspace,compile_h3_scene
    root=Path(workspace).absolute();out=Path(output).absolute()
    if out.exists() or out.is_symlink() or any(p.is_symlink() for p in out.parents):raise CompilerQAError('ACTUAL_PAINT_OUTPUT_EXISTS_OR_SYMLINK')
    checked=require_h3_workspace(root);envelope=json.loads((root/'CHECKED_SCENE.json').read_text())
    if asdict(target)!=envelope['target']:raise CompilerQAError('ACTUAL_PAINT_TARGET_MISMATCH')
    compiled=compile_h3_scene(envelope['document'],target=target,motion_preference=envelope['motion_preference']);raw=compiled.effective_document
    n=(raw['duration_ms']*target.fps+999)//1000
    if n>2400 or n*len(raw['elements'])>12000:raise CompilerQAError('ACTUAL_PAINT_WORK_BUDGET_NO_SAMPLED_PASS')
    from .font_coverage import system_font_coverage,source_texts
    font_evidence=system_font_coverage(source_texts(raw))
    if not font_evidence['passed']:raise CompilerQAError('ACTUAL_PAINT_FONT_COVERAGE_BLOCKED')
    before=collect_installed_toolchain(root,node=node,browser=browser)
    for name in ('@remotion/bundler','@remotion/renderer'):
        if 'node_modules/'+name not in before['installed_packages']:raise CompilerQAError('ACTUAL_PAINT_RENDERER_DEPENDENCY_MISSING:'+name)
    out.mkdir(parents=True)
    nonce=secrets.token_hex(24);support=Path(__file__).parent/'qa_support'
    with tempfile.TemporaryDirectory(prefix='bie-real-paint-') as td:
        stage=Path(td)/'project'
        shutil.copytree(root,stage,symlinks=True,ignore=shutil.ignore_patterns('out','render-evidence','validation-runs'))
        capture=stage/'capture-output';capture.mkdir()
        (stage/'public').mkdir(exist_ok=True)
        # hash every staged dependency; an interrupted copy or changed root cannot slip in.
        staged=collect_installed_toolchain(stage,node=node,browser=browser);require_same_toolchain(before,staged)
        req={'workspace':'/work','output':'/work/capture-output','browser':str(browser),'remotion_version':target.remotion_version,
             'composition_id':'BieQA'+digest(raw['scene_id'])[:16],'width':target.width,'height':target.height,
             'fps':target.fps,'frame_count':n,'nonce':nonce,
             'equationFonts':{e['element_id']:e['props'].get('font_size',32) for e in raw['elements'] if e['element_type']=='equation'}}
        # JS measurement lives in checked-in trusted helpers, not the ingested book.
        # Enable checkJs=false only for helper DOM code in a separate module; original strict TS config unchanged.
        helper='export const baseMeasure = '+(support/'layout_measure.js').read_text().strip()+';\nexport const paintMeasure = '+(support/'paint_measure.js').read_text().strip()+';\n'
        # Observer entry imports a typed trusted JS helper. No user source typechecks are relaxed.
        source=capture_entry(req,'(options: {frame:number;equationFonts:Record<string,number>}) => baseMeasureImpl(options)','(options: {frame:number;equationFonts:Record<string,number>}) => paintMeasureImpl(options)')
        source='import {baseMeasure as baseMeasureImpl,paintMeasure as paintMeasureImpl} from "./qa-paint-helper";\n'+source
        (stage/'qa-capture-entry.tsx').write_text(source)
        (stage/'qa-paint-helper.js').write_text(helper)
        (stage/'qa-paint-helper.d.ts').write_text('export function baseMeasure(options:{frame:number;equationFonts:Record<string,number>}):unknown[];\nexport function paintMeasure(options:{frame:number;equationFonts:Record<string,number>}):unknown[];\n')
        (stage/'capture-request.json').write_bytes(canonical_json(req))
        # Strict TS remains enabled. Only trusted JS measurement helpers use declarations.
        stage_cfg=json.loads((stage/'tsconfig.json').read_text())
        stage_cfg['compilerOptions'].update(allowJs=True,checkJs=False)
        stage_cfg['include']+=['qa-capture-entry.tsx','qa-paint-helper.js','qa-paint-helper.d.ts']
        (stage/'tsconfig.json').write_bytes(canonical_json(stage_cfg))
        tc=isolated_typecheck(stage,node=node,evidence_directory=out/'typecheck')
        if tc.status!='PASS':raise CompilerQAError('ACTUAL_PAINT_TYPECHECK_BLOCKED:'+tc.status)
        process,kernel=run_isolated([str(node),'/engine/app/bie/compiler/qa_support/remotion_paint_capture.cjs','/work/capture-request.json'],
                                   workspace=stage,engine=Path(__file__).resolve().parents[3],writable=['capture-output'],
                                   policy=policy or WorkerPolicy(),timeout_s=max(120,min(3600,n*4)),max_output_bytes=8*1024**2)
        (out/'PROCESS.json').write_bytes(canonical_json({'process':asdict(process),'kernel_policy':kernel}))
        if not process.process.passed:raise CompilerQAError('ACTUAL_PAINT_EXECUTION_BLOCKED:'+process.outcome+':'+process.process.stderr[:500])
        data=json.loads((capture/'RESULT.json').read_text())
        if data.get('scope')!='REAL_REMOTION_INSTRUMENTED_UNCHANGED_SCENE' or data.get('nonce')!=nonce or data.get('real_remotion') is not True or data.get('browser_errors')!=[]:
            raise CompilerQAError('ACTUAL_PAINT_PRODUCER_MISMATCH')
        frames=data['frames']
        if [f['frame'] for f in frames]!=list(range(n)):raise CompilerQAError('ACTUAL_PAINT_FRAME_COVERAGE')
        records=[];paint=[]
        for f in frames:
            if f['image']!=f"frame-{f['frame']:06d}.png" or file_hash(capture/f['image'])[0]!=f['image_sha256']:raise CompilerQAError('ACTUAL_PAINT_IMAGE_CHANGED')
            m=f['measurement']
            if m['frame']!=f['frame'] or m['nonce']!=nonce or m['fonts_ready'] is not True:raise CompilerQAError('ACTUAL_PAINT_MEASUREMENT_IDENTITY')
            records+=m['records'];paint+=m['paint_records']
        if file_hash(capture/'captured.mp4')[0]!=data['media_sha256']:raise CompilerQAError('ACTUAL_PAINT_MEDIA_CHANGED')
        report={'scope':DECLARED_SCOPE,'scene_identity':digest(raw),'manifest_sha256':checked.manifest_sha256,
                'width':target.width,'height':target.height,'fps':target.fps,'frame_count':n,'fonts_ready':True,'browser_errors':[],'records':records}
        fit=inspect_owner_fit(report,raw,target,checked.manifest_sha256)
        quality=inspect_paint_quality(paint,element_ids=[e['element_id'] for e in raw['elements']],frame_count=n)
        # Inventory after executable consumption, before any witness can be minted.
        after=collect_installed_toolchain(root,node=node,browser=browser);require_same_toolchain(before,after)
        require_same_toolchain(before,collect_installed_toolchain(stage,node=node,browser=browser))
        require_h3_workspace(root,expected_scene_fingerprint=checked.scene_fingerprint)
        shutil.copytree(capture,out/'capture',ignore=shutil.ignore_patterns('bundle'))
        evidence={'schema_version':'bie.actual-paint-verified-run.v1','source_manifest_sha256':checked.manifest_sha256,
                  'toolchain_sha256':before['identity_sha256'],'capture_entry_sha256':file_hash(stage/'qa-capture-entry.tsx')[0],
                  'helper_sha256':file_hash(stage/'qa-paint-helper.js')[0],'producer_sha256':file_hash(support/'remotion_paint_capture.cjs')[0],
                  'frame_count':n,'fit':fit,'paint':quality,'font_coverage':font_evidence,'kernel_policy':kernel,'real_remotion':True,
                  'scope':'PROCESS_OWNED_INSTRUMENTED_ORIGINAL_SCENE','learning_quality':'NOT_EVALUATED','accepted':False}
        (out/'EVIDENCE.json').write_bytes(canonical_json(evidence))
        return ActualPaintWitness(checked.manifest_sha256,digest(evidence),before['identity_sha256'],n,fit['passed'] and quality['passed'],evidence,_SEAL)
