"""H3 checked source: exhaustive layer geometry, explicit variants, isolated math.

Source PASS is not content-fit/paint PASS. Every use recomputes the host/input/
variant/source identity. Legacy H1/H2 diagnostic envelopes cannot enter Remotion
execution after the full dependency check. These local receipts are not signatures.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict,replace
from pathlib import Path
from functools import partial
from hashlib import sha256
import json,os,shutil,tempfile
from .artifact_hashing import canonical_json,confined_path
from .qa_common import CompilerQAError,QAFinding,ordered_findings,digest
from .qa_scene_compile import CompilerQATarget,compile_scene_for_qa
from .checked_scene_compile import CheckedSceneReceipt
from .scene_ir_loader import load_scene_ir_payload
from .deterministic_codegen import plan_deterministic_codegen,write_codegen_plan
from .compile_diagnostics_mapping import build_source_map
from .generated_code_regression import probe_typescript_sources
from .frame_layout import evaluate_frame_layout
from .reduced_motion import resolve_reduced_motion
from .host_toolchain import collect_host_toolchain
from .isolated_typesetting import isolated_typeset_latex

SCHEMA='bie.checked-scene.h3.v1'
VERSION='1.3.0-comp-h3'

@dataclass(frozen=True)
class H3CompiledScene:
    bundle: object
    receipt: CheckedSceneReceipt
    effective_document: dict
    layout: dict
    motion: dict
    host: dict
    @property
    def codegen(self):return self.bundle.codegen


def compile_h3_scene(payload,*,target=None,motion_preference='standard'):
    target=target or replace(CompilerQATarget(),compiler_version=VERSION)
    if target.compiler_version!=VERSION:
        raise CompilerQAError('H3_TARGET_VERSION_REQUIRED: use the versioned H3 source producer')
    loaded=load_scene_ir_payload(payload);raw=loaded.document.to_dict()
    effective,motion=resolve_reduced_motion(raw,target,motion_preference)
    layout=evaluate_frame_layout(effective,target)
    host=collect_host_toolchain()
    typesetter=partial(isolated_typeset_latex,expected_host=host)
    base=compile_scene_for_qa(effective,target=target,typesetter=typesetter,
                             frozen_simulation_frames=motion['frozen_simulation_frames'],layer_qa_tags=True)
    identity={'schema_version':'bie.h3-source-identity.v1','original_input_sha256':digest(payload),
              'original_document_fingerprint':loaded.document.fingerprint,
              'effective_document_fingerprint':base.scene_fingerprint,
              'host_identity':host['identity_sha256'],'motion_preference':motion_preference,
              'layer_geometry_passed':layout['passed'],'content_fit_status':'NOT_RUN',
              'real_remotion_status':'NOT_RUN','accepted':False}
    extra={'src/bie-h3-identity.json':identity,'src/bie-h3-layout.json':layout,
           'src/bie-h3-motion.json':motion,'src/bie-h3-host-toolchain.json':host}
    plan=plan_deterministic_codegen(scene_fingerprint=base.scene_fingerprint,compiler_version=VERSION,
                deterministic_seed=target.seed,component_snapshot=base.codegen.component_snapshot,
                files=[(f.path,f.content) for f in base.codegen.files]+[(p,canonical_json(v).decode()+'\n') for p,v in extra.items()])
    mapping=build_source_map(scene_fingerprint=base.scene_fingerprint,files=plan.files,spans=base.source_map.spans)
    context=replace(base.context,dependency_identity=digest({'base':base.context.dependency_identity,
                    'host':host['identity_sha256'],'motion':motion_preference,'layout_policy':layout['policy']}))
    probe=probe_typescript_sources(plan.files)
    findings=ordered_findings((*base.findings,*probe.findings,*[QAFinding(**f) for f in layout['findings']]))
    passed=base.source_contract_passed and layout['passed'] and probe.status=='PASS' and not any(f.severity=='ERROR' for f in findings)
    bundle=replace(base,codegen=plan,source_map=mapping,context=context,findings=findings,source_contract_passed=passed,
                   scope='H3_CHECKED_SCENE_SOURCE_NOT_PAINT_OR_PRODUCT_ACCEPTANCE')
    receipt=CheckedSceneReceipt(base.scene_fingerprint,plan.manifest_sha256,
             'H3_SOURCE_GATE_PASS_NOT_PRODUCT_ACCEPTED' if passed else 'H3_SOURCE_GATE_BLOCKED',passed,findings,probe.status,VERSION)
    if collect_host_toolchain()['identity_sha256']!=host['identity_sha256']:
        raise CompilerQAError('H3_TOOLCHAIN_CHANGED_DURING_COMPILE')
    return H3CompiledScene(bundle,receipt,effective,layout,motion,host)


def _envelope(payload,target,preference,result):
    return {'schema_version':SCHEMA,'document':payload,'target':asdict(target),'motion_preference':preference,
            'effective_document_identity':digest(result.effective_document),
            'host_identity':result.host['identity_sha256'],'receipt':asdict(result.receipt),'accepted':False}


def publish_h3_scene(payload,destination,*,target=None,motion_preference='standard'):
    target=target or replace(CompilerQATarget(),compiler_version=VERSION)
    result=compile_h3_scene(payload,target=target,motion_preference=motion_preference)
    if not result.receipt.source_gate_passed:
        raise CompilerQAError('H3_SOURCE_PUBLICATION_BLOCKED: '+', '.join(f.code for f in result.receipt.findings if f.severity=='ERROR'))
    destination=Path(destination).absolute()
    if destination.exists() or destination.is_symlink() or any(p.is_symlink() for p in destination.parents):
        raise CompilerQAError('destination exists or has symlink parents')
    destination.parent.mkdir(parents=True,exist_ok=True)
    staging=Path(tempfile.mkdtemp(prefix='.bie-h3-',dir=destination.parent))
    try:
        write_codegen_plan(result.codegen,staging)
        data=canonical_json(_envelope(payload,target,motion_preference,result))
        if len(data)>4*1024*1024:raise CompilerQAError('H3_ENVELOPE_TOO_LARGE')
        (staging/'CHECKED_SCENE.json').write_bytes(data)
        destination.mkdir(exist_ok=False)
        try:os.replace(staging,destination)
        except BaseException:
            destination.rmdir();raise
    finally:
        if staging.exists():shutil.rmtree(staging)
    return result.receipt


def require_h3_workspace(root,*,expected_scene_fingerprint=None,render_request=None):
    root=Path(root).absolute()
    if root.is_symlink() or not root.is_dir() or any(p.is_symlink() for p in root.parents):
        raise CompilerQAError('H3_WORKSPACE_INVALID')
    marker=root/'CHECKED_SCENE.json'
    if marker.is_symlink() or not marker.is_file() or marker.stat().st_size>4*1024*1024:
        raise CompilerQAError('H3_SOURCE_REQUIRED: checked H3 source must precede real execution')
    raw=json.loads(marker.read_text())
    if raw.get('schema_version')!=SCHEMA or raw.get('accepted') is not False:
        raise CompilerQAError('H3_SOURCE_REQUIRED: older source receipts are diagnostic-only')
    # Detect changed host before doing potentially expensive regeneration.
    if raw.get('host_identity')!=collect_host_toolchain()['identity_sha256']:
        raise CompilerQAError('H3_HOST_IDENTITY_CHANGED: publish a fresh project under the current toolchain')
    target=CompilerQATarget(**raw['target']);preference=raw['motion_preference']
    result=compile_h3_scene(raw['document'],target=target,motion_preference=preference)
    if not result.receipt.source_gate_passed:raise CompilerQAError('H3_REVALIDATION_BLOCKED')
    if canonical_json(raw)!=canonical_json(_envelope(raw['document'],target,preference,result)):
        raise CompilerQAError('H3_ENVELOPE_TAMPERED')
    if expected_scene_fingerprint is not None and expected_scene_fingerprint!=result.receipt.scene_fingerprint:
        raise CompilerQAError('H3_SCENE_IDENTITY_MISMATCH')
    if render_request is not None:
        expected={'composition_id':'BieQA'+digest(result.bundle.scene_id)[:16],
                  'width':target.width,'height':target.height,'fps':target.fps,
                  'duration_in_frames':(result.effective_document['duration_ms']*target.fps+999)//1000}
        if asdict(render_request.composition)!=expected or render_request.entrypoint!='src/index.ts':
            raise CompilerQAError('RENDER_REQUEST_SOURCE_MISMATCH')
        if render_request.props_file is not None:raise CompilerQAError('RUNTIME_PROPS_NOT_BOUND')
    expected={f.path:f for f in result.codegen.files}
    for name,source in expected.items():
        p=confined_path(root,name)
        if not p.is_file() or p.is_symlink() or sha256(p.read_bytes()).hexdigest()!=source.sha256:
            raise CompilerQAError('GENERATED_SOURCE_TAMPERED: '+name)
    manifest={'scene_fingerprint':result.codegen.scene_fingerprint,'compiler_version':result.codegen.compiler_version,
              'deterministic_seed':result.codegen.deterministic_seed,'manifest_sha256':result.codegen.manifest_sha256,
              'files':[{'path':f.path,'sha256':f.sha256} for f in result.codegen.files],'accepted':False}
    path=confined_path(root,'CODEGEN_MANIFEST.json',must_exist=True)
    if path.is_symlink() or canonical_json(json.loads(path.read_text()))!=canonical_json(manifest):
        raise CompilerQAError('CODEGEN_MANIFEST_TAMPERED')
    extras={'CHECKED_SCENE.json','CODEGEN_MANIFEST.json','package-lock.json','smoke-request.json','full-request.json'}
    for p in root.rglob('*'):
        rel=p.relative_to(root)
        if rel.parts[0]=='node_modules':continue # Full node tree attestation is a separate unresolved requirement.
        if p.is_symlink():raise CompilerQAError('WORKSPACE_SYMLINK_FORBIDDEN: '+rel.as_posix())
        if rel.parts[0] in {'render-evidence','out','validation-runs'} and p.is_file():
            if p.suffix.lower() not in {'.mp4','.png','.jpg','.json','.jsonl','.log','.env','.txt'}:
                raise CompilerQAError('UNINSPECTED_EXECUTABLE_OUTPUT: '+rel.as_posix())
            continue
        if p.is_file() and rel.as_posix() not in expected and rel.as_posix() not in extras:
            raise CompilerQAError('UNINSPECTED_WORKSPACE_FILE: '+rel.as_posix())
    return result.receipt
