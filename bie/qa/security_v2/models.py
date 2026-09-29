"""Data-only generated-code security scope. Policy/trust are operator-provisioned."""
from dataclasses import dataclass, asdict
from ..release_v2.contracts import ArtifactRef, ContractError, token, integer, choice, sha256, digest, tuple_tokens
from ..repair_v2.models import Snapshot, seq, unique

PROBES = ('allowed_read','allowed_write','outside_read','outside_write','parent_traversal',
          'symlink_read','inherited_fd','environment','ipv4_socket','ipv6_socket','unix_socket',
          'spawn','exec','privilege','namespace','ptrace','file_limit','descriptor_limit')
CONTROLS = ('private_root','non_root','no_capabilities','no_new_privs','seccomp_filter',
            'clean_environment','closed_descriptors','cpu_limit','memory_limit','file_limit','descriptor_limit')

@dataclass(frozen=True, slots=True)
class CodeUnit:
    artifact_id: str
    language: str
    profile: str
    def __post_init__(self):
        token(self.artifact_id,'artifact_id')
        choice(self.language,('PYTHON','TYPESCRIPT','TSX','JAVASCRIPT','NPM_MANIFEST'),'language')
        choice(self.profile,('PURE','DATA','REVIEW','MANIFEST'),'profile')
        if (self.language=='PYTHON' and self.profile not in ('PURE','REVIEW')) or (self.language in ('TYPESCRIPT','TSX','JAVASCRIPT') and self.profile not in ('DATA','REVIEW')) or (self.language=='NPM_MANIFEST' and self.profile!='MANIFEST'):
            raise ContractError('SEC_PROFILE_LANGUAGE')

@dataclass(frozen=True, slots=True)
class Dependency:
    name: str
    version: str
    artifact_id: str
    def __post_init__(self):
        import re
        if type(self.name) is not str or not re.fullmatch(r'(?:@[a-z0-9_-]+/)?[a-z0-9_.-]+',self.name) or self.name.startswith('.'):
            raise ContractError('SEC_DEPENDENCY_NAME')
        if type(self.version) is not str or not re.fullmatch(r'\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?',self.version):
            raise ContractError('SEC_DEPENDENCY_VERSION')
        token(self.artifact_id,'dependency_artifact')

@dataclass(frozen=True, slots=True)
class SecurityPolicy:
    policy_id: str
    snapshot_digest: str
    units: tuple[CodeUnit,...]
    dependencies: tuple[Dependency,...]=()
    approved_scripts: tuple[tuple[str,str],...]=()
    parser_node_sha256: str=''
    parser_typescript_sha256: str=''
    max_source_bytes: int=262144
    max_ast_nodes: int=20000
    max_receipt_age_seconds: int=3600
    def __post_init__(self):
        token(self.policy_id,'policy_id');sha256(self.snapshot_digest,'snapshot_digest')
        seq(self.units,CodeUnit,'units',1,128);unique(self.units,'artifact_id','units')
        seq(self.dependencies,Dependency,'dependencies',0,128);unique(self.dependencies,'name','dependencies')
        unique(self.dependencies,'artifact_id','dependency_artifacts')
        if type(self.approved_scripts) is not tuple or len(self.approved_scripts)>16:raise ContractError('SEC_SCRIPTS_TYPE')
        names=set()
        for x in self.approved_scripts:
            if type(x) is not tuple or len(x)!=2 or any(type(v) is not str or not v or len(v)>1024 for v in x):raise ContractError('SEC_SCRIPT_RECORD')
            if x[0] in names:raise ContractError('SEC_SCRIPT_DUPLICATE')
            names.add(x[0])
        if bool(self.parser_node_sha256)!=bool(self.parser_typescript_sha256):raise ContractError('SEC_PARSER_PAIR')
        for h in (self.parser_node_sha256,self.parser_typescript_sha256):
            if h:sha256(h,'parser_hash')
        integer(self.max_source_bytes,'max_source_bytes',1,1048576)
        integer(self.max_ast_nodes,'max_ast_nodes',1,100000)
        integer(self.max_receipt_age_seconds,'max_receipt_age_seconds',1,604800)
    @property
    def content_digest(self):return digest(asdict(self))

@dataclass(frozen=True, slots=True)
class SecurityRequest:
    snapshot: Snapshot
    sandbox_evidence: ArtifactRef|None=None
    def __post_init__(self):
        if type(self.snapshot) is not Snapshot:raise ContractError('SEC_SNAPSHOT_TYPE')
        if self.sandbox_evidence is not None:
            if type(self.sandbox_evidence) is not ArtifactRef or self.sandbox_evidence.role!='report':raise ContractError('SEC_SANDBOX_REF')
            if self.sandbox_evidence.artifact_id in {a.artifact_id for a in self.snapshot.artifacts} or self.sandbox_evidence.path in {a.path for a in self.snapshot.artifacts}:raise ContractError('SEC_RECEIPT_ALIAS')
    @property
    def content_digest(self):return digest(dict(snapshot=self.snapshot.content_digest,sandbox_evidence=asdict(self.sandbox_evidence) if self.sandbox_evidence else None))
