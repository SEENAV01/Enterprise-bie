"""Non-executing AST inspection; a clean scan is not a security sandbox or CVE scan."""
from __future__ import annotations
import ast, hashlib, json, os, re, subprocess, tempfile, unicodedata
from pathlib import Path
from dataclasses import dataclass
from ..release_v2.contracts import ContractError
from ..source_v2.codec import loads

@dataclass(frozen=True, slots=True)
class Toolchain:
    node: str
    node_sha256: str
    typescript: str
    typescript_sha256: str
    def validate(self):
        for path,expected in ((self.node,self.node_sha256),(self.typescript,self.typescript_sha256)):
            p=Path(path)
            if not p.is_absolute() or not p.is_file() or p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest()!=expected:
                raise ContractError('SEC_PARSER_TOOL_IDENTITY')

# Capability identifiers: conservative syntax finding, not taint analysis.
PY_DANGER={'eval','exec','compile','__import__','open','input','breakpoint','globals','locals','vars','getattr','setattr','delattr','dir','help','exit','quit','memoryview'}
PY_MODULES={'os','sys','subprocess','socket','ctypes','multiprocessing','threading','importlib','pickle','marshal','shelve','http','urllib','requests','builtins','pathlib','shutil','tempfile','io'}
PURE_CALLS={'abs','min','max','round','len','sum','all','any','sorted'}
PURE_NODES={ast.Module,ast.FunctionDef,ast.arguments,ast.arg,ast.Return,ast.Assign,ast.Expr,ast.Name,ast.Load,ast.Store,ast.Constant,ast.BinOp,ast.UnaryOp,ast.BoolOp,ast.Compare,ast.If,ast.IfExp,ast.List,ast.Tuple,ast.Dict,ast.Subscript,ast.Slice,ast.Call,ast.keyword,ast.Pass,
 ast.Add,ast.Sub,ast.Mult,ast.Div,ast.FloorDiv,ast.Mod,ast.Pow,ast.USub,ast.UAdd,ast.Not,ast.And,ast.Or,ast.Eq,ast.NotEq,ast.Lt,ast.LtE,ast.Gt,ast.GtE,ast.Is,ast.IsNot,ast.In,ast.NotIn}

def scan_python(text,profile,max_nodes):
    findings=[];imports=[]
    def add(code,severity='BLOCKER',line=0):
        x=dict(code=code,severity=severity,line=line)
        if x not in findings:findings.append(x)
    try:tree=ast.parse(text)
    except (SyntaxError,ValueError,RecursionError,MemoryError):return [dict(code='SEC_PARSE_ERROR',severity='BLOCKER',line=0)],[],0
    nodes=list(ast.walk(tree))
    if len(nodes)>max_nodes:return [dict(code='SEC_AST_LIMIT',severity='BLOCKER',line=0)],[],len(nodes)
    for n in nodes:
        line=getattr(n,'lineno',0)
        if isinstance(n,(ast.Import,ast.ImportFrom)):
            names=[a.name for a in n.names] if isinstance(n,ast.Import) else [n.module or '']
            imports.extend(names)
            # Imports are deliberately unsupported in this pure producer profile.
            add('SEC_IMPORT_REQUIRES_REVIEW','REVIEW',line)
            if any(x.split('.')[0] in PY_MODULES for x in names):add('SEC_CAPABILITY_IMPORT',line=line)
        if isinstance(n,ast.Name) and (n.id in PY_DANGER or n.id in PY_MODULES or n.id.startswith('__')):add('SEC_CAPABILITY_NAME',line=line)
        if isinstance(n,ast.Attribute):
            if n.attr.startswith('__') or n.attr in {'system','popen','spawn','fork','execve','connect','environ','read_text','write_text'}:add('SEC_CAPABILITY_ATTRIBUTE',line=line)
            else:add('SEC_ATTRIBUTE_REQUIRES_REVIEW','REVIEW',line)
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and (n.decorator_list or n.name.startswith('__')):add('SEC_DECORATOR_OR_SPECIAL_FUNCTION',line=line)
        if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store) and n.id in PURE_CALLS:add('SEC_BUILTIN_SHADOW',line=line)
        if isinstance(n,ast.arg) and (n.arg in PURE_CALLS or n.arg.startswith('__')):add('SEC_BUILTIN_SHADOW',line=line)
        if isinstance(n,ast.Call) and not (isinstance(n.func,ast.Name) and n.func.id in PURE_CALLS):add('SEC_CALL_REQUIRES_REVIEW','REVIEW',line)
        if profile=='PURE':
            if type(n) not in PURE_NODES:add('SEC_PURE_PROFILE_VIOLATION',line=line)
            if isinstance(n,ast.Call) and not (isinstance(n.func,ast.Name) and n.func.id in PURE_CALLS):add('SEC_PURE_PROFILE_VIOLATION',line=line)
    if profile=='REVIEW':add('SEC_GENERAL_CODE_REVIEW','REVIEW')
    return findings,sorted(set(imports)),len(nodes)

def scan_typescript(text,language,profile,max_nodes,toolchain):
    if type(toolchain) is not Toolchain:raise ContractError('SEC_TYPESCRIPT_PARSER_REQUIRED')
    toolchain.validate()
    helper=Path(__file__).with_name('typescript_scan.cjs')
    # Only the parser executes; generated text is data on stdin, never evaluated.
    request=json.dumps(dict(text=text,language=language,profile=profile,max_nodes=max_nodes))
    env={'PATH':str(Path(toolchain.node).parent),'LANG':'C.UTF-8','HOME':'/nonexistent'}
    with tempfile.TemporaryDirectory(prefix='bie-sec-parse-') as d:
        try:
            p=subprocess.run([toolchain.node,'--max-old-space-size=128',str(helper),toolchain.typescript],input=request,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,cwd=d,env=env,timeout=8,close_fds=True)
        except subprocess.TimeoutExpired as e:raise ContractError('SEC_PARSER_TIMEOUT') from e
    if p.returncode!=0 or len(p.stdout)>2*1024*1024:raise ContractError('SEC_PARSER_FAILED')
    toolchain.validate()
    raw=loads(p.stdout.encode())
    if type(raw) is not dict or set(raw)!={'findings','imports','nodes','parser_version'}:raise ContractError('SEC_PARSER_RECEIPT')
    return raw['findings'],raw['imports'],raw['nodes']

def scan_manifest(text,dependencies,approved_scripts):
    f=[]
    def add(c,s='BLOCKER'):f.append(dict(code=c,severity=s,line=0))
    try:v=loads(text.encode())
    except ContractError:return [dict(code='SEC_MANIFEST_PARSE',severity='BLOCKER',line=0)],[],0
    if type(v) is not dict:return [dict(code='SEC_MANIFEST_OBJECT',severity='BLOCKER',line=0)],[],0
    scripts=v.get('scripts',{})
    if type(scripts) is not dict or any(type(k) is not str or type(x) is not str or dict(approved_scripts).get(k)!=x for k,x in scripts.items()):add('SEC_UNAPPROVED_INSTALL_OR_BUILD_SCRIPT')
    permitted={d.name:d.version for d in dependencies};imports=[]
    for key in ('dependencies','devDependencies','peerDependencies','optionalDependencies'):
        ds=v.get(key,{})
        if type(ds) is not dict:add('SEC_MANIFEST_DEPENDENCIES');continue
        for name,version in ds.items():
            imports.append(name)
            if type(version) is not str or permitted.get(name)!=version:add('SEC_UNPINNED_DEPENDENCY')
    if any(k in v for k in ('bin','gypfile','workspaces','overrides','resolutions','bundledDependencies','bundleDependencies')):add('SEC_MANIFEST_CAPABILITY_REVIEW','REVIEW')
    # Permission to execute a script is not established merely by seeing this file.
    if scripts:add('SEC_APPROVED_SCRIPTS_STILL_REQUIRE_ISOLATION','REVIEW')
    return f,sorted(set(imports)),len(v)

def scan(data,unit,policy,toolchain=None):
    if len(data)>policy.max_source_bytes:raise ContractError('SEC_SOURCE_LIMIT')
    try:text=data.decode('utf-8',errors='strict')
    except UnicodeDecodeError as e:raise ContractError('SEC_SOURCE_UTF8') from e
    if not text.strip():raise ContractError('SEC_EMPTY_SOURCE')
    if '\x00' in text or any(unicodedata.category(x)=='Cf' for x in text):raise ContractError('SEC_HIDDEN_CONTROL')
    if unit.language=='PYTHON':return scan_python(text,unit.profile,policy.max_ast_nodes)
    if unit.language=='NPM_MANIFEST':return scan_manifest(text,policy.dependencies,policy.approved_scripts)
    return scan_typescript(text,unit.language,unit.profile,policy.max_ast_nodes,toolchain)
