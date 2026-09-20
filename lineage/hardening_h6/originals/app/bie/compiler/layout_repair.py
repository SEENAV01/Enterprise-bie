"""H4-004/005: bounded, measured repair and explicit upstream handoff.

The local Chromium/API-double probe is always run by this process. An uploaded
measurement JSON cannot authorize candidate selection or publication. Results are
source/local-layout evidence, never actual Remotion or product acceptance.
"""
from __future__ import annotations
from copy import deepcopy
from dataclasses import asdict, replace
from pathlib import Path
import json
import shutil

from .artifact_hashing import canonical_json
from .hardened_scene_compile import compile_h3_scene, publish_h3_scene, require_h3_workspace, VERSION
from .host_toolchain import file_identity
from .layout_browser import ChromiumLayoutProbe
from .layout_measurements import inspect_owner_fit
from .layout_repair_contracts import candidates, validate_policy, verify_repair, canonical_scene, default_policy
from .qa_common import CompilerQAError, digest
from .qa_scene_compile import CompilerQATarget


def _new_directory(path: Path) -> Path:
    path = path.absolute()
    if path.exists() or path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise CompilerQAError('REPAIR_OUTPUT_EXISTS_OR_SYMLINK')
    path.mkdir(parents=True, exist_ok=False)
    return path


def _write(path: Path, payload: dict) -> None:
    path.write_bytes(canonical_json(payload) + b'\n')


def _run_candidates(payload, policy, target, probe, output, *, motion_preference='standard', screenshots=False):
    """Private test seam. Public entry point constructs its own real local probe."""
    original, policy = validate_policy(payload, policy)
    attempts = []; selected = None; selected_receipt = None; selected_fit = None
    runtime_block = None
    for candidate in candidates(original, policy):
        row={'candidate_index':candidate.index, 'effective_identity':digest(candidate.document),
             'invariants':candidate.invariants, 'source_gate_passed':False, 'local_fit_passed':False}
        try:
            compiled=compile_h3_scene(candidate.document,target=target,motion_preference=motion_preference)
            row['source_gate_passed']=compiled.receipt.source_gate_passed
            row['source_manifest_sha256']=compiled.codegen.manifest_sha256
            row['codes']=sorted({f.code for f in compiled.receipt.findings if f.severity=='ERROR'})
            if compiled.receipt.source_gate_passed:
                folder=output/f'candidate-{candidate.index:03d}'
                measured=probe.measure(compiled,target,folder,screenshots=screenshots)
                fit=inspect_owner_fit(measured,compiled.effective_document,target,compiled.codegen.manifest_sha256)
                _write(folder/'OWNER_FIT.json',fit)
                row.update(local_fit_passed=fit['passed'], measurement_sha256=digest(measured),
                           measurement_path=f'candidate-{candidate.index:03d}/MEASUREMENTS.json',
                           fit_sha256=digest(fit), records_checked=fit['records_checked'],
                           scope=fit['scope'], codes=sorted({f['code'] for f in fit['findings']}))
                if fit['passed']:
                    selected=candidate.document;selected_receipt=compiled.receipt;selected_fit=fit
        except (OSError, ValueError, TimeoutError) as exc:
            row['codes']=[str(exc).split(':',1)[0]]
            row['error']=str(exc)[:2000]
            # Dependency, execution and observation failures are not proof a
            # candidate has bad geometry. Do not turn environment errors into a
            # request to rewrite a lesson or skip to a fabricated success.
            runtime_block=str(exc)
        attempts.append(row)
        if selected is not None or runtime_block is not None: break
    status='ENVIRONMENT_OR_VALIDATOR_BLOCKED' if runtime_block else ('LOCAL_MEASURED_CANDIDATE' if selected else 'UPSTREAM_REVISION_REQUIRED')
    result={'schema_version':'bie.layout-repair-run.v1','status':status,
            'original_identity':digest(original),'policy_identity':digest(policy),'target':asdict(target),
            'motion_preference':motion_preference,'attempt_count':len(attempts),'candidate_budget':policy['max_candidates'],
            'attempts':attempts,'selected_index':attempts[-1]['candidate_index'] if selected else None,
            'selected_identity':digest(selected) if selected else None,
            'selected_source_receipt':asdict(selected_receipt) if selected_receipt else None,
            'local_fit_passed':bool(selected_fit and selected_fit['passed']),
            'runtime_block':runtime_block,'source_published':False,'real_react':False,'real_remotion':False,
            'release_authorized':False,'accepted':False,
            'search_scope':'BOUNDED_AUTHORIZED_RECTANGLE_AND_PRESENTATION_CANDIDATES_NOT_GLOBAL_LAYOUT_OPTIMUM'}
    _write(output/'ORIGINAL_SCENE.json',original);_write(output/'POLICY.json',policy)
    if selected is not None:
        verify_repair(original,selected,policy)
        _write(output/'EFFECTIVE_SCENE.json',selected)
    elif runtime_block is None:
        revision={'schema_version':'bie.upstream-layout-revision.v1','original_scene_identity':digest(original),
                  'scene_id':original['scene_id'],'source_refs':original['source_refs'],'reasoning_refs':original['reasoning_refs'],
                  'policy_identity':digest(policy),'owner_ids':sorted(policy['owners']),
                  'blocking_codes':sorted({code for row in attempts for code in row['codes']}),
                  'attempt_count':len(attempts),'search_is_bounded':True,
                  'requested_actions':['Provide an explicit revised visual layout with additional permitted space or scene structure.',
                                       'Preserve all text, labels, units, equations, narration, timing and source/reasoning links; changed instructional timing requires upstream approval.'],
                  'automatic_text_deletion':False,'automatic_font_reduction':False,
                  'automatic_pagination_or_timing_change':False,'accepted':False}
        _write(output/'UPSTREAM_REVISION_REQUEST.json',revision)
        result['upstream_revision_request_sha256']=digest(revision)
    _write(output/'REPAIR_RESULT.json',result)
    return result,selected


def repair_scene_layout(payload: dict, policy: dict | None, evidence_directory, *, target=None,
                        browser='/usr/bin/chromium', motion_preference='standard', screenshots=False) -> dict:
    target=target or replace(CompilerQATarget(),compiler_version=VERSION)
    policy=default_policy(payload) if policy is None else policy
    validate_policy(payload,policy)
    output=_new_directory(Path(evidence_directory))
    try:
        with ChromiumLayoutProbe(browser) as probe:
            result,_=_run_candidates(payload,policy,target,probe,output,
                                      motion_preference=motion_preference,screenshots=screenshots)
        return result
    except Exception as exc:
        # Boundary failure is retained as a block, never converted to success.
        result={'schema_version':'bie.layout-repair-run.v1','status':'ENVIRONMENT_OR_VALIDATOR_BLOCKED',
                'runtime_block':str(exc),'local_fit_passed':False,'source_published':False,
                'real_remotion':False,'release_authorized':False,'accepted':False}
        _write(output/'REPAIR_RESULT.json',result)
        return result


def repair_and_publish(payload, policy, destination, evidence_directory, *, target=None,
                       browser='/usr/bin/chromium', motion_preference='standard', screenshots=False):
    destination=Path(destination).absolute();output=Path(evidence_directory).absolute()
    if destination==output or destination in output.parents or output in destination.parents:
        raise CompilerQAError('REPAIR_PATHS_MUST_BE_SEPARATE')
    if destination.exists() or destination.is_symlink() or any(p.is_symlink() for p in destination.parents):
        raise CompilerQAError('REPAIR_DESTINATION_EXISTS_OR_SYMLINK')
    target=target or replace(CompilerQATarget(),compiler_version=VERSION)
    result=repair_scene_layout(payload,policy,output,target=target,browser=browser,
                               motion_preference=motion_preference,screenshots=screenshots)
    if result['status']!='LOCAL_MEASURED_CANDIDATE': return result
    original=json.loads((output/'ORIGINAL_SCENE.json').read_text())
    effective=json.loads((output/'EFFECTIVE_SCENE.json').read_text())
    checked_policy=json.loads((output/'POLICY.json').read_text())
    proof=verify_repair(original,effective,checked_policy)
    if proof['original_identity']!=result['original_identity'] or proof['effective_identity']!=result['selected_identity']:
        raise CompilerQAError('REPAIR_RESULT_IDENTITY_CHANGED')
    receipt=publish_h3_scene(effective,destination,target=target,motion_preference=motion_preference)
    if receipt.manifest_sha256!=result['selected_source_receipt']['manifest_sha256']:
        # Never publish a regenerated project different from the measured source.
        shutil.rmtree(destination)
        raise CompilerQAError('REPAIR_SOURCE_CHANGED_DURING_PUBLICATION')
    evidence=destination/'validation-runs'/'h4-layout-repair';evidence.mkdir(parents=True)
    # Only source-bound selected metadata, not repeated unsuccessful projects.
    for name in ['ORIGINAL_SCENE.json','EFFECTIVE_SCENE.json','POLICY.json']:
        shutil.copyfile(output/name,evidence/name)
    chosen = 'candidate-' + format(result['selected_index'], '03d')
    shutil.copytree(output/chosen, evidence/chosen)
    result['source_published']=True
    _write(evidence/'REPAIR_RESULT.json',result);_write(output/'REPAIR_RESULT.json',result)
    require_h3_workspace(destination)
    return result


def verify_repaired_workspace(root: Path) -> dict:
    """Integrity/replay check, explicitly NOT a trusted measurement attestation."""
    source=require_h3_workspace(root)
    evidence=Path(root)/'validation-runs'/'h4-layout-repair'
    values={}
    for name in ('ORIGINAL_SCENE','EFFECTIVE_SCENE','POLICY','REPAIR_RESULT'):
        p=evidence/(name+'.json')
        if not p.is_file() or p.is_symlink() or p.stat().st_size>8*1024*1024:
            raise CompilerQAError('REPAIR_EVIDENCE_MISSING_OR_INVALID')
        values[name]=json.loads(p.read_text())
    proof=verify_repair(values['ORIGINAL_SCENE'],values['EFFECTIVE_SCENE'],values['POLICY'])
    result=values['REPAIR_RESULT']
    envelope=json.loads((Path(root)/'CHECKED_SCENE.json').read_text())
    if canonical_scene(envelope['document'])!=canonical_scene(values['EFFECTIVE_SCENE']):
        raise CompilerQAError('REPAIR_EFFECTIVE_SOURCE_MISMATCH')
    if (result['selected_source_receipt']['manifest_sha256']!=source.manifest_sha256 or
        result['original_identity']!=proof['original_identity'] or result['selected_identity']!=proof['effective_identity'] or
        result['policy_identity']!=proof['policy_identity'] or result.get('accepted') is not False or result.get('release_authorized') is not False or
        result.get('real_remotion') is not False or result.get('source_published') is not True):
        raise CompilerQAError('REPAIR_EVIDENCE_IDENTITY_MISMATCH')
    if result.get('real_react') is not False or result.get('status') != 'LOCAL_MEASURED_CANDIDATE' or result.get('local_fit_passed') is not True:
        raise CompilerQAError('REPAIR_SCOPE_OR_STATUS_MISMATCH')
    if result.get('target') != envelope['target'] or result.get('motion_preference') != envelope['motion_preference']:
        raise CompilerQAError('REPAIR_TARGET_IDENTITY_MISMATCH')
    compiled=compile_h3_scene(envelope['document'], target=CompilerQATarget(**envelope['target']), motion_preference=envelope['motion_preference'])
    index=result.get('selected_index')
    if type(index) is not int or not 0 <= index < len(result.get('attempts',[])):
        raise CompilerQAError('REPAIR_SELECTED_ATTEMPT_INVALID')
    attempt=result['attempts'][index]
    folder=evidence/('candidate-'+format(index,'03d'))
    measured=json.loads((folder/'MEASUREMENTS.json').read_text())
    fit=inspect_owner_fit(measured,compiled.effective_document,CompilerQATarget(**envelope['target']),compiled.codegen.manifest_sha256)
    if not fit['passed'] or digest(measured)!=attempt.get('measurement_sha256') or digest(fit)!=attempt.get('fit_sha256'):
        raise CompilerQAError('REPAIR_MEASUREMENT_CHANGED')
    for shot in measured.get('screenshots',[]):
        relative=Path(shot['path'])
        if relative.is_absolute() or '..' in relative.parts or len(relative.parts)!=1 or file_identity(folder/relative)!=shot['sha256']:
            raise CompilerQAError('REPAIR_SCREENSHOT_CHANGED')
    return {'schema_version':'bie.repaired-source-integrity.v1','source_recomputed':True,'invariants':proof,
            'actual_measurement_attested':False,'release_authorized':False,'accepted':False}
