"""HARD028 actual staged rebuild/recapture and paired regression execution.

Uses H6's independently authorized changes, fresh working copies at every stage,
and immutable program identities. An injected diagnostic cannot become native
media/game evidence. This engine returns review evidence, not publication.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
from .common import *
from .runtime import Program,run_trusted,NativeWorkerProfile,native_worker

@dataclass(frozen=True)
class Stage:
    stage_id:str
    role:str
    program:Program
    output_paths:tuple[str,...]
    native_profile:NativeWorkerProfile|None=None
    native_checkout:str|None=None
    def __post_init__(self):
        token(self.stage_id,'stage')
        require(self.role in ('compile','render','capture','regression'),'H7_STAGE_ROLE')
        require(type(self.program) is Program,'H7_STAGE_PROGRAM')
        require(type(self.output_paths) is tuple and self.output_paths and len(self.output_paths)==len(set(self.output_paths)),'H7_STAGE_OUTPUTS')
        for p in self.output_paths:safe_relative_path(p)
        require((self.native_profile is None)==(self.native_checkout is None),'H7_NATIVE_STAGE_PAIR')
        if self.native_profile is not None:
            require(type(self.native_profile) is NativeWorkerProfile and Path(self.native_checkout).is_absolute(),'H7_NATIVE_STAGE_PROFILE')
            require(Path(self.program.script_path).is_relative_to(Path(self.native_checkout)),'H7_NATIVE_SCRIPT_OUTSIDE_ENGINE')

@dataclass(frozen=True)
class RebuildPolicy:
    baseline_rows:tuple[dict,...]
    stages:tuple[Stage,...]
    expected_case_ids:tuple[str,...]
    target_case_ids:tuple[str,...]
    require_native:bool=True
    def __post_init__(self):
        require(type(self.baseline_rows) is tuple and bool(self.baseline_rows),'H7_REBUILD_BASELINE')
        require(type(self.stages) is tuple and len(self.stages)==4,'H7_STAGE_CENSUS')
        require([s.role for s in self.stages]==['compile','render','capture','regression'],'H7_STAGE_ORDER')
        exact_ids(tuple(s.stage_id for s in self.stages),'H7_STAGE_IDS')
        exact_ids(self.expected_case_ids,'H7_CASE_CENSUS');exact_ids(self.target_case_ids,'H7_TARGET_CENSUS')
        require(set(self.target_case_ids)<=set(self.expected_case_ids),'H7_UNKNOWN_TARGET')
        require(type(self.require_native) is bool,'H7_NATIVE_REQUIRED_TYPE')
    @property
    def content_digest(self):return digest(asdict(self))


def _cases(folder,record,policy):
    result=strict_object(regular_bytes(folder,'result.json'))
    fields(result,('execution_id','run_id','cases'),'H7_CASE_RESULT_FIELDS')
    require(result['execution_id']==record['execution_id'] and result['run_id']==record['run_id'],'H7_REUSED_CAPTURE_ID')
    rows=result['cases'];require(type(rows) is list and len(rows)==len(policy.expected_case_ids),'H7_RESULT_CASE_CENSUS')
    require({r['case_id'] for r in rows}==set(policy.expected_case_ids) and len({r['case_id'] for r in rows})==len(rows),'H7_RESULT_CASE_CENSUS')
    for r in rows:
        fields(r,('case_id','status'),'H7_CASE_FIELDS');require(r['status'] in ('PASS','FAIL'),'H7_CASE_NOT_EXECUTED')
    return {r['case_id']:r['status'] for r in rows}


def execute_stage(stage,inputs,output,run_id):
    """An out-of-band native profile selects the real isolated worker; no fallback.

    Native stage commands take explicit {INPUT_ROOT}/{OUTPUT_ROOT} arguments.
    Native program scripts must live in the approved read-only engine checkout.
    Diagnostic stages use the separately labelled trusted runner.
    """
    if stage.native_profile is None:
        return run_trusted(stage.program,inputs,output,run_id=run_id)
    stage.program.verify();before=inventory(inputs)
    require(not any(r['path'].startswith('outputs/') for r in before),'H7_NATIVE_OUTPUT_PREEXISTS')
    native_out=Path(inputs)/'outputs';native_out.mkdir(exist_ok=False)
    execution_id=new_id()
    command=tuple(a.replace('{INPUT_ROOT}',str(inputs)).replace('{OUTPUT_ROOT}',str(native_out)).replace('{EXECUTION_ID}',execution_id).replace('{RUN_ID}',run_id) for a in stage.program.argv)
    result=native_worker(stage.native_checkout,stage.native_profile,command,inputs,output=Path(output).with_name(Path(output).name+'-control'))
    current=[r for r in inventory(inputs) if not r['path'].startswith('outputs/')]
    require(current==before,'H7_NATIVE_STAGE_INPUT_CHANGED')
    rows=inventory(native_out);copy_verified(native_out,output,rows);stage.program.verify()
    rec=dict(result['process']);rec.update(control_execution_id=rec['execution_id'],execution_id=execution_id,outputs=rows,output_digest=digest(rows),input_digest=digest(before),inputs=before,
        native_executed=result.get('native_executed') is True,kind='NATIVE_ISOLATED_WORKER',run_id=run_id,
        kernel_proof=result.get('proof'),error=None if result.get('native_executed') is True else 'NATIVE_WORKER_BLOCKED')
    return rec

def rebuild(change,scope,review,verifier,now,root,output,policy):
    require(type(change) is Change and type(policy) is RebuildPolicy,'H7_REBUILD_TYPE')
    authorize(change,scope,review,verifier,now)
    original=inventory(root);require(original==list(policy.baseline_rows),'H7_BASELINE_INVENTORY')
    require(not any(r['path']=='upstream' or r['path'].startswith('upstream/') for r in original),'H7_RESERVED_UPSTREAM_PATH')
    require(change.target.path in {r['path'] for r in original},'H7_CHANGE_TARGET_MISSING')
    require(identity(regular_bytes(root,change.target.path))==change.target.sha256,'H7_CHANGE_PREIMAGE')
    out=Path(output);out.mkdir(parents=True,exist_ok=False);side_results={};errors=[]
    for side in ('baseline','candidate'):
        side_root=out/side;side_root.mkdir();base=copy_verified(root,side_root/'source',original)
        if side=='candidate':(base/change.target.path).write_bytes(change.payload)
        expected=inventory(base)
        for p in scope.protected_paths:
            require(regular_bytes(base,p)==regular_bytes(root,p),'H7_PROTECTED_REPAIR_CHANGED')
        previous=[];records=[];side_cases={};run='rebuild-'+side+'-'+new_id()
        for stage in policy.stages:
            inp=copy_verified(base,side_root/(stage.stage_id+'-input'),expected)
            for prior,folder in previous:
                for row in prior['outputs']:
                    data=regular_bytes(folder,row['path']);require(identity(data)==row['sha256'],'H7_UPSTREAM_CAPTURE_CHANGED')
                    p=inp/'upstream'/prior['stage_id']/row['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
            folder=side_root/(stage.stage_id+'-output')
            rec=execute_stage(stage,inp,folder,run);rec['stage_id']=stage.stage_id;rec['role']=stage.role;records.append(rec)
            if rec['error'] or {r['path'] for r in rec['outputs']}!=set(stage.output_paths):
                errors.append('H7_REBUILD_STAGE_FAILED');break
            previous.append((rec,folder))
            if stage.role=='regression':side_cases=_cases(folder,rec,policy)
        require(inventory(base)==expected,'H7_REBUILD_BASE_CHANGED')
        side_results[side]=dict(records=records,cases=side_cases,input_digest=digest(expected))
    if not errors:
        b=side_results['baseline']['cases'];c=side_results['candidate']['cases']
        if any(b[k]!='FAIL' for k in policy.target_case_ids):errors.append('H7_TARGET_NOT_REPRODUCED')
        if any(v!='PASS' for v in c.values()):errors.append('H7_REPAIR_REGRESSION')
        all_ids=[r['execution_id'] for side in side_results.values() for r in side['records']]
        if len(all_ids)!=len(set(all_ids)):errors.append('H7_REUSED_EXECUTION')
    require(inventory(root)==original,'H7_REBUILD_MUTATED_ORIGINAL')
    native_ok=all(len(v['records'])==4 and all(r.get('native_executed') is True for r in v['records']) for v in side_results.values())
    if policy.require_native and not native_ok:errors.append('H7_NATIVE_REBUILD_NOT_EXECUTED')
    details=dict(policy_digest=policy.content_digest,change_digest=change.content_digest,required_checks=change.required_checks,
        invalidated=change.invalidates,sides=side_results,old_evidence_reused=False,native_rebuild_verified=native_ok,
        staged_review_only=True)
    return local_report('BIE-QA-HARD-028',change.binding,details,errors)
