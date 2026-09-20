"""H3-004 content identities for the supported Python math adapter.

Selected compiler/interpreter/backend/native/font files are hashed, not shipped.
This is deliberately not a whole-OS or installed-node_modules attestation.
"""
from __future__ import annotations
from functools import lru_cache
from pathlib import Path
import importlib,importlib.metadata,platform,sys,sysconfig,os
from hashlib import sha256
from .qa_common import digest, CompilerQAError

CONTROLS={'LANG':'C.UTF-8','LC_ALL':'C.UTF-8','MPLBACKEND':'Agg','OMP_NUM_THREADS':'1',
          'OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMEXPR_NUM_THREADS':'1',
          'PYTHONHASHSEED':'0','SOURCE_DATE_EPOCH':'0','TZ':'UTC'}
PACKAGES=('matplotlib','numpy','PIL','pyparsing','cycler','kiwisolver','contourpy','fontTools','packaging','dateutil')
DIST={'PIL':'pillow','fontTools':'fonttools','dateutil':'python-dateutil'}


@lru_cache(maxsize=8192)
def _hashed(path,signature):
    h=sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def file_identity(path):
    p=Path(path).resolve(strict=True);a=p.stat()
    sig=(a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)
    value=_hashed(str(p),sig);b=p.stat()
    if sig!=(b.st_dev,b.st_ino,b.st_size,b.st_mtime_ns,b.st_ctime_ns):
        raise CompilerQAError('TOOLCHAIN_CHANGED_DURING_HASH: '+p.name)
    return value


def _package_files(module):
    m=importlib.import_module(module)
    root=Path(m.__file__).resolve().parent
    extensions={'.py','.so','.pyd','.dll','.dylib','.ttf','.otf','.afm','.json','.mplstyle'}
    paths=[]
    for p in root.rglob('*'):
        if not p.is_file() or '__pycache__' in p.parts or any(x in {'tests','test','testing'} for x in p.relative_to(root).parts):continue
        if p.suffix in extensions or p.name=='matplotlibrc':paths.append(p)
    # Wheels may keep linked OpenBLAS/libpng/freetype binaries next to the package.
    for dirname in (module+'.libs',module.lower()+'.libs',DIST.get(module,module)+'.libs'):
        extra=root.parent/dirname
        if extra.is_dir():paths.extend(p for p in extra.rglob('*') if p.is_file())
    return root,sorted(set(paths))


def collect_host_toolchain():
    files={};versions={}
    for mod in PACKAGES:
        try:
            root,paths=_package_files(mod)
            versions[mod]=importlib.metadata.version(DIST.get(mod,mod))
        except (ImportError,importlib.metadata.PackageNotFoundError) as exc:
            raise CompilerQAError('HOST_TOOLCHAIN_UNAVAILABLE: '+mod) from exc
        for p in paths:
            try:rel=p.relative_to(root).as_posix()
            except ValueError:rel='linked-libs/'+p.parent.name+'/'+p.name
            files[mod+'/'+rel]=file_identity(p)
    compiler=Path(__file__).resolve().parent
    for p in sorted(compiler.rglob('*.py')):
        files['bie.compiler/'+p.relative_to(compiler).as_posix()]=file_identity(p)
    # Scene decoding is part of source identity and therefore included explicitly.
    scene=compiler.parent/'scene_ir'
    for p in sorted(scene.rglob('*.py')):
        files['bie.scene_ir/'+p.relative_to(scene).as_posix()]=file_identity(p)
    interpreter=Path(sys.executable).resolve()
    binaries={'python':file_identity(interpreter)}
    shared=sysconfig.get_config_var('LDLIBRARY');libdir=sysconfig.get_config_var('LIBDIR')
    if shared and libdir and (Path(libdir)/shared).is_file():binaries['libpython']=file_identity(Path(libdir)/shared)
    from matplotlib import ft2font
    record={'schema_version':'bie.host-toolchain.v1','scope':'SELECTED_PYTHON_COMPILER_MATH_INPUT_CONTENTS',
            'python':{'implementation':platform.python_implementation(),'version':platform.python_version(),
                      'cache_tag':sys.implementation.cache_tag,'byteorder':sys.byteorder},
            'platform':{'system':platform.system(),'machine':platform.machine(),'libc':list(platform.libc_ver())},
            'versions':versions,'freetype_version':ft2font.__freetype_version__,'binaries':binaries,
            'files':dict(sorted(files.items())),'environment_controls':CONTROLS.copy(),
            'excluded':['whole_os_kernel','all_system_shared_libraries','node_modules','browser_font_fallbacks','network_isolation'],
            'font_bytes_distributed':False,'accepted':False}
    record['identity_sha256']=digest(record)
    return record


def validate_host_identity(identity):
    if not isinstance(identity,dict) or 'identity_sha256' not in identity:raise CompilerQAError('HOST_IDENTITY_INVALID')
    expected=identity['identity_sha256'];body={k:v for k,v in identity.items() if k!='identity_sha256'}
    if digest(body)!=expected:raise CompilerQAError('HOST_IDENTITY_TAMPERED')
    return expected
