from __future__ import annotations
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Mapping
from ..ids import require_id,require_text
from ..canonical import fingerprint
from .errors import GameBuildError

def _sha(v):
    if not isinstance(v,str) or len(v)!=64 or any(c not in '0123456789abcdef' for c in v):raise GameBuildError('GAME_BUILD_SHA256')
    return v

def safe_relative(path):
    if not isinstance(path,str) or not path or '\\' in path or path.startswith('/') or any(ord(c)<32 for c in path):raise GameBuildError('GAME_BUILD_PATH')
    p=PurePosixPath(path)
    if ':' in path or path!=p.as_posix():raise GameBuildError('GAME_BUILD_PATH')
    if p.is_absolute() or any(x in ('','.','..') for x in p.parts):raise GameBuildError('GAME_BUILD_PATH')
    return p.as_posix()

@dataclass(frozen=True)
class BuildPolicy:
    compile_timeout_seconds:int=60;browser_timeout_ms:int=30000;process_timeout_seconds:int=30;max_artifact_bytes:int=5_000_000;max_package_bytes:int=25_000_000;allow_external_network:bool=False;product_accepted:bool=False
    process_cpu_seconds:int=45;process_memory_bytes:int=1_500_000_000;process_max_processes:int=128;process_max_open_files:int=256;browser_sandbox_uid:int=65534;browser_sandbox_gid:int=65534;require_browser_sandbox:bool=True
    def validate(self):
        for v in (self.compile_timeout_seconds,self.process_timeout_seconds,self.max_artifact_bytes,self.max_package_bytes,self.process_cpu_seconds,self.process_memory_bytes,self.process_max_processes,self.process_max_open_files):
            if type(v) is not int or v<=0:raise GameBuildError('GAME_BUILD_POLICY_RANGE')
        if type(self.browser_timeout_ms) is not int or self.browser_timeout_ms<1000:raise GameBuildError('GAME_BUILD_BROWSER_TIMEOUT')
        if type(self.browser_sandbox_uid) is not int or type(self.browser_sandbox_gid) is not int or self.browser_sandbox_uid<=0 or self.browser_sandbox_gid<=0:raise GameBuildError('GAME_BUILD_BROWSER_SANDBOX_ID')
        if self.require_browser_sandbox is not True or self.allow_external_network or self.product_accepted:raise GameBuildError('GAME_BUILD_POLICY_WEAKENED')
        return self

@dataclass(frozen=True)
class ToolIdentity:
    name:str;path:str;version:str;executable_sha256:str
    def validate(self):
        require_id(self.name,'GAME_BUILD_TOOL_NAME');require_text(self.path,'GAME_BUILD_TOOL_PATH');require_text(self.version,'GAME_BUILD_TOOL_VERSION');_sha(self.executable_sha256);return self

@dataclass(frozen=True)
class PackageArtifact:
    path:str;size_bytes:int;sha256:str;media_type:str;source_kind:str
    def validate(self):
        safe_relative(self.path)
        if type(self.size_bytes) is not int or self.size_bytes<0:raise GameBuildError('GAME_BUILD_ARTIFACT_SIZE')
        _sha(self.sha256);require_text(self.media_type,'GAME_BUILD_ARTIFACT_MEDIA');require_id(self.source_kind,'GAME_BUILD_ARTIFACT_SOURCE');return self

@dataclass(frozen=True)
class RuntimePackageManifest:
    schema_version:str;compiler_receipt_id:str;compiler_bundle_fingerprint:str;toolchain_fingerprint:str;artifacts:tuple[PackageArtifact,...];entrypoint:str;package_fingerprint:str;deterministic:bool=True;external_network:bool=False;product_accepted:bool=False;manifest_payload_sha256:str='';asset_bindings:tuple[tuple[str,str,str],...]=()
    def validate(self):
        require_id(self.schema_version,'GAME_BUILD_MANIFEST_SCHEMA');require_id(self.compiler_receipt_id,'GAME_BUILD_COMPILER_RECEIPT');safe_relative(self.entrypoint)
        if not self.compiler_bundle_fingerprint.startswith('sha256:') or not self.toolchain_fingerprint.startswith('sha256:') or not self.package_fingerprint.startswith('sha256:'):raise GameBuildError('GAME_BUILD_MANIFEST_FINGERPRINT')
        paths=[a.path for a in self.artifacts];[a.validate() for a in self.artifacts]
        if paths!=sorted(paths) or len(paths)!=len(set(paths)) or self.entrypoint not in paths:raise GameBuildError('GAME_BUILD_MANIFEST_ARTIFACTS')
        if self.manifest_payload_sha256 and (len(self.manifest_payload_sha256)!=64 or any(c not in '0123456789abcdef' for c in self.manifest_payload_sha256)):raise GameBuildError('GAME_BUILD_MANIFEST_SELF_HASH')
        if len({r for r,_,_ in self.asset_bindings})!=len(self.asset_bindings):raise GameBuildError('GAME_BUILD_ASSET_BINDING_DUPLICATE')
        if not self.deterministic or self.external_network or self.product_accepted:raise GameBuildError('GAME_BUILD_MANIFEST_SCOPE')
        return self

@dataclass(frozen=True)
class BuildReceipt:
    receipt_id:str;task_id:str;input_fingerprint:str;output_fingerprint:str;toolchain_fingerprint:str;evidence_refs:tuple[str,...];deterministic:bool=True;product_accepted:bool=False
    def validate(self):
        require_id(self.receipt_id,'GAME_BUILD_RECEIPT_ID');require_id(self.task_id,'GAME_BUILD_TASK_ID')
        for v in (self.input_fingerprint,self.output_fingerprint,self.toolchain_fingerprint):
            if not v.startswith('sha256:'):raise GameBuildError('GAME_BUILD_RECEIPT_HASH')
        if not self.evidence_refs or not self.deterministic or self.product_accepted:raise GameBuildError('GAME_BUILD_RECEIPT_SCOPE')
        return self

@dataclass(frozen=True)
class BrowserEvidence:
    target:str;execution_mode:str;browser_version:str;studio_grade:bool;slide_deck:bool;entity_count:int;external_requests:tuple[str,...];console_errors:tuple[str,...];page_errors:tuple[str,...];runtime_binding_keys:tuple[str,...];bundle_sha256:str;product_accepted:bool=False;sandbox_uid:int=0;sandbox_no_new_privs:bool=False;renderer_seccomp:bool=False;canonical_worker_blob:str=''
    def validate(self):
        require_text(self.target,'GAME_BUILD_BROWSER_TARGET');require_id(self.execution_mode,'GAME_BUILD_BROWSER_MODE');require_text(self.browser_version,'GAME_BUILD_BROWSER_VERSION');_sha(self.bundle_sha256)
        if not self.studio_grade or self.slide_deck or self.entity_count<1 or self.external_requests or self.console_errors or self.page_errors or not self.runtime_binding_keys or self.product_accepted:raise GameBuildError('GAME_BUILD_BROWSER_EVIDENCE')
        if self.sandbox_uid<=0 or not self.sandbox_no_new_privs or not self.renderer_seccomp or len(self.canonical_worker_blob)!=40:raise GameBuildError('GAME_BUILD_BROWSER_SANDBOX_EVIDENCE')
        return self

@dataclass(frozen=True)
class InteractionSimulationReceipt:
    mechanic_id:str;mechanic_receipt_id:str;semantic_event_id:str;state_patch_fingerprint:str;compiled_event_present:bool;motion_ids:tuple[str,...];causal:bool;product_accepted:bool=False
    def validate(self):
        for x,c in ((self.mechanic_id,'GAME_BUILD_MECH_ID'),(self.mechanic_receipt_id,'GAME_BUILD_MECH_RECEIPT'),(self.semantic_event_id,'GAME_BUILD_EVENT_ID')):require_id(x,c)
        if not self.state_patch_fingerprint.startswith('sha256:') or not self.compiled_event_present or not self.motion_ids or not self.causal or self.product_accepted:raise GameBuildError('GAME_BUILD_INTERACTION_RECEIPT')
        return self

@dataclass(frozen=True)
class ReplayEvidence:
    run_fingerprint:str;initial_snapshot_id:str;final_snapshot_id:str;transition_receipt_ids:tuple[str,...];success:bool;identical_second_run:bool;product_accepted:bool=False
    def validate(self):
        if not self.run_fingerprint.startswith('sha256:'):raise GameBuildError('GAME_BUILD_REPLAY_HASH')
        for x in (self.initial_snapshot_id,self.final_snapshot_id):require_id(x,'GAME_BUILD_REPLAY_SNAPSHOT')
        if not self.transition_receipt_ids or not self.success or not self.identical_second_run or self.product_accepted:raise GameBuildError('GAME_BUILD_REPLAY_EVIDENCE')
        return self

@dataclass(frozen=True)
class ExceptionEvidence:
    origin:str;exception_name:str;message_code:str;stack_sha256:str;caught:bool;raw_stack_persisted:bool=False;product_accepted:bool=False
    def validate(self):
        if self.origin not in ('node','browser'):raise GameBuildError('GAME_BUILD_EXCEPTION_ORIGIN')
        require_text(self.exception_name,'GAME_BUILD_EXCEPTION_NAME');require_id(self.message_code,'GAME_BUILD_EXCEPTION_CODE');_sha(self.stack_sha256)
        if not self.caught or self.raw_stack_persisted or self.product_accepted:raise GameBuildError('GAME_BUILD_EXCEPTION_SCOPE')
        return self
