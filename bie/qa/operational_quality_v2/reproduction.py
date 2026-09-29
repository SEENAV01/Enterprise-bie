"""HARD032 restoring approved dependency files and measured host comparison.

No network install, resolver or smudge hook is invoked. A complete dependency
closure is an externally supplied requirement, not inferred from selected files.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
import os,platform,struct,sys
from pathlib import Path
from .common import *
from .runtime import Program,run_trusted
from .dependencies import DependencyPolicy,verify_dependencies


def host_profile(tools):
    require(type(tools) is tuple and tools,'H7_TOOL_INVENTORY')
    observed=[]
    for name,path in tools:
        token(name,'tool');p=Path(path).resolve(strict=True)
        row=tool_identity(p);observed.append(dict(name=name,sha256=row['sha256'],bytes=row['bytes']))
    require(len({r['name'] for r in observed})==len(observed),'H7_TOOL_ALIAS')
    os_release=Path('/etc/os-release').read_bytes() if Path('/etc/os-release').exists() else b''
    return dict(schema_version='bie.qa.measured-host/1',system=platform.system(),machine=platform.machine(),kernel=platform.release(),
        libc=list(platform.libc_ver()),python=list(sys.version_info[:3]),pointer_bits=struct.calcsize('P')*8,
        os_release_sha256=identity(os_release),tools=sorted(observed,key=lambda r:r['name']))

@dataclass(frozen=True)
class ReproductionPolicy:
    dependency_policy:DependencyPolicy
    host:dict
    tools:tuple[tuple[str,str],...]
    output_paths:tuple[str,...]
    required_runs:int=2
    cross_host_required:bool=False
    def __post_init__(self):
        require(type(self.dependency_policy) is DependencyPolicy,'H7_REPRO_DEPENDENCIES')
        require(type(self.host) is dict and self.host.get('schema_version')=='bie.qa.measured-host/1','H7_REPRO_HOST')
        integer(self.required_runs,'runs',2,5);require(type(self.cross_host_required) is bool,'H7_CROSS_HOST_FLAG')
        require(type(self.output_paths) is tuple and self.output_paths and len(set(self.output_paths))==len(self.output_paths),'H7_REPRO_OUTPUTS')
        for p in self.output_paths:safe_relative_path(p)
    @property
    def content_digest(self):return digest(asdict(self))


def reproduce(source,output,program,policy,review,*,approved_review_digest,now):
    require(type(policy) is ReproductionPolicy and type(program) is Program,'H7_REPRO_TYPE')
    dep=verify_dependencies(source,policy.dependency_policy,review,approved_review_digest=approved_review_digest,now=now)
    require(not dep['blocked_packages'] and not dep['unknown_packages'],'H7_REPRO_DEPENDENCY_BLOCK')
    require(host_profile(policy.tools)==policy.host,'H7_HOST_DRIFT')
    out=Path(output);out.mkdir(parents=True,exist_ok=False);records=[]
    for i in range(policy.required_runs):
        inputs=copy_verified(source,out/f'input-{i}',list(policy.dependency_policy.file_rows))
        rec=run_trusted(program,inputs,out/f'output-{i}',run_id='repro-'+str(i))
        require(host_profile(policy.tools)==policy.host,'H7_HOST_DRIFT')
        records.append(rec)
    errors=['H7_CROSS_HOST_EVIDENCE_MISSING'] if policy.cross_host_required else []
    for r in records:
        if r['error']:errors.append('H7_REPRO_EXECUTION_FAILED')
        if {x['path'] for x in r['outputs']}!=set(policy.output_paths):errors.append('H7_REPRO_OUTPUT_CENSUS')
    if len({r['output_digest'] for r in records})!=1:errors.append('H7_REPRO_NONDETERMINISTIC')
    if len({r['execution_id'] for r in records})!=len(records):errors.append('H7_REPRO_REPLAYED_PROCESS')
    require(inventory(source)==list(policy.dependency_policy.file_rows),'H7_REPRO_SOURCE_CHANGED')
    return dict(schema_version='bie.qa.dependency-reproduction/1',policy_digest=policy.content_digest,host=policy.host,dependency_review=dep,
        runs=records,errors=sorted(set(errors)),status='BLOCKED' if errors or policy.cross_host_required else 'REVIEW_REQUIRED',
        cross_host_verified=False,cross_host_required=policy.cross_host_required,full_os_image_rebuilt=False,
        restored_dependency_files=len(policy.dependency_policy.file_rows),product_accepted=False)
