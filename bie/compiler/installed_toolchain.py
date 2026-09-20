"""H7: complete local dependency-byte inventory, not publisher authentication.

The checked producer owns package.json. The npm lock and every installed file
(including optional native modules and internal .bin links) enter the execution
identity. Missing required dependencies, external links and live mutation block.
No implicit installation, executable discovery from user PATH or cached hashes.
"""
from __future__ import annotations
from pathlib import Path
import hashlib, json, os, re, stat, subprocess
from .qa_common import CompilerQAError, digest
from .artifact_hashing import canonical_json


def fail(code, detail):
    raise CompilerQAError(code + ': ' + str(detail))


def file_hash(path):
    path=Path(path)
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK)
    try:
        before=os.fstat(fd)
        if not stat.S_ISREG(before.st_mode): fail('TOOLCHAIN_FILE_TYPE',path)
        h=hashlib.sha256()
        while True:
            b=os.read(fd,1024*1024)
            if not b: break
            h.update(b)
        after=os.fstat(fd)
        if (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)!=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns):
            fail('TOOLCHAIN_CHANGED_DURING_HASH',path)
        return h.hexdigest(),before.st_size
    finally: os.close(fd)


def tree_inventory(root, *, max_files=100000, max_bytes=2*1024**3):
    root=Path(root).absolute()
    if root.is_symlink() or not root.is_dir() or any(p.is_symlink() for p in root.parents):
        fail('TOOLCHAIN_ROOT_INVALID',root)
    rows=[]; total=0
    def scan(folder):
        nonlocal total
        for p in sorted(folder.iterdir()):
            rel=p.relative_to(root).as_posix(); info=p.lstat()
            if stat.S_ISLNK(info.st_mode):
                link=os.readlink(p)
                try: dest=p.resolve(strict=True)
                except (OSError,RuntimeError): fail('TOOLCHAIN_BROKEN_LINK',rel)
                if not dest.is_relative_to(root) or not dest.is_file(): fail('TOOLCHAIN_EXTERNAL_OR_DIRECTORY_LINK',rel)
                h,n=file_hash(dest); rows.append({'path':rel,'kind':'internal_file_link','target':dest.relative_to(root).as_posix(),'link_text':link,'sha256':h,'bytes':n})
            elif stat.S_ISDIR(info.st_mode): scan(p)
            elif stat.S_ISREG(info.st_mode):
                h,n=file_hash(p);total+=n;rows.append({'path':rel,'kind':'file','sha256':h,'bytes':n,'executable':bool(info.st_mode&0o111)})
            else: fail('TOOLCHAIN_FILE_TYPE',rel)
            if len(rows)>max_files or total>max_bytes: fail('TOOLCHAIN_BUDGET_EXCEEDED','full inventory required; no sampling')
    scan(root)
    return {'files':rows,'file_count':len(rows),'bytes':total,'tree_sha256':digest(rows)}


def collect_installed_toolchain(workspace, *, node, browser, extra_tools=()):
    root=Path(workspace).absolute()
    if root.is_symlink() or any(p.is_symlink() for p in root.parents):fail('TOOLCHAIN_ROOT_INVALID',root)
    for name in ('package.json','package-lock.json'):
        p=root/name
        if not p.is_file() or p.is_symlink() or p.stat().st_size>32*1024**2:fail('TOOLCHAIN_LOCK_REQUIRED',name)
    package=json.loads((root/'package.json').read_text());lock=json.loads((root/'package-lock.json').read_text())
    if lock.get('lockfileVersion') not in (2,3) or not isinstance(lock.get('packages'),dict):fail('TOOLCHAIN_LOCK_INVALID','npm v2/v3 lock required')
    from .dependency_lock import validate_package_lock
    validate_package_lock(root/'package-lock.json',root/'package.json')
    deps={**package.get('dependencies',{}),**package.get('devDependencies',{})}
    packages=lock['packages']; installed={}; missing=[]
    for loc, meta in sorted(packages.items()):
        if not loc:continue
        if not loc.startswith('node_modules/') or '..' in Path(loc).parts or meta.get('link'):
            fail('TOOLCHAIN_LOCK_LOCATION',loc)
        p=root/loc/'package.json'
        if not p.exists():
            if meta.get('optional') is True:missing.append(loc);continue
            fail('TOOLCHAIN_DEPENDENCY_MISSING',loc)
        if p.is_symlink():fail('TOOLCHAIN_PACKAGE_LINK',loc)
        data=json.loads(p.read_text())
        if not isinstance(meta.get('version'),str) or data.get('version')!=meta['version']:fail('TOOLCHAIN_VERSION_MISMATCH',loc)
        installed[loc]=meta['version']
    for name,wanted in sorted(deps.items()):
        loc='node_modules/'+name
        if loc not in installed:fail('TOOLCHAIN_DIRECT_DEPENDENCY_MISSING',name)
        if name in {'remotion','react','react-dom','typescript'} or name.startswith('@remotion/'):
            if not re.fullmatch(r'\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?',wanted) or installed[loc]!=wanted:
                fail('TOOLCHAIN_EXACT_VERSION_REQUIRED',name)
    if installed.get('node_modules/react') != installed.get('node_modules/react-dom'):fail('TOOLCHAIN_REACT_PAIR','different versions')
    rv=installed.get('node_modules/remotion')
    if not rv or any(v!=rv for k,v in installed.items() if k.startswith('node_modules/@remotion/')):fail('TOOLCHAIN_REMOTION_PAIR','mixed versions')
    inventory=tree_inventory(root/'node_modules')
    # Every actual package directory is lock-described, not a hidden npm/global adapter.
    for row in inventory['files']:
        path=row['path']
        if path=='package.json' or (path.endswith('/package.json') and '/node_modules/' not in path and len(Path(path).parts) in (2,3)) or '/node_modules/' in path and path.endswith('/package.json'):
            loc='node_modules/'+path.removesuffix('/package.json')
            # Packages sometimes ship sample package.json; only package roots get matched.
            parts=Path(path).parts
            root_location=(len(parts)==2 or len(parts)==3 and parts[0].startswith('@') or 'node_modules' in parts[:-1])
            if root_location and loc not in packages:fail('TOOLCHAIN_UNLOCKED_PACKAGE',loc)
    tools={}; runtime_resources={}; native_paths=set()
    for label,value in [('node',node),('browser',browser),*extra_tools]:
        p=Path(value)
        if not p.is_absolute() or not p.is_file():fail('TOOLCHAIN_EXECUTABLE_MISSING',label)
        dest=p.resolve(strict=True);h,n=file_hash(dest)
        tools[label]={'sha256':h,'bytes':n,'basename':dest.name}
        with dest.open('rb') as stream:
            if stream.read(4)==b'\x7fELF':native_paths.add(dest)
        if label=='browser' and dest.name=='chromium':
            real=Path('/usr/lib/chromium/chromium')
            if real.is_file():
                h,n=file_hash(real);tools['browser_native']={'sha256':h,'bytes':n,'basename':real.name}
                runtime_resources['chromium_distribution']=tree_inventory(real.parent,max_files=20000,max_bytes=1024**3)
                native_paths.add(real)
    native_libraries={}
    # Operator-selected executables only. Generated/book source cannot choose ldd targets.
    for binary in sorted(native_paths):
        r=subprocess.run(['/usr/bin/ldd',str(binary)],env={'PATH':'/usr/bin:/bin','LANG':'C'},capture_output=True,text=True,timeout=10)
        if r.returncode or 'not found' in r.stdout:fail('TOOLCHAIN_NATIVE_DEPENDENCY_MISSING',binary.name)
        for name in re.findall(r'(?:=>\s*)?(/[^\s()]+)',r.stdout):
            q=Path(name).resolve();h,n=file_hash(q);native_libraries[str(q)]={'basename':q.name,'sha256':h,'bytes':n}
    runtime_resources['native_linked_libraries']=sorted(native_libraries.values(),key=lambda x:(x['basename'],x['sha256']))
    if Path('/etc/ld.so.cache').is_file():
        h,n=file_hash('/etc/ld.so.cache');runtime_resources['dynamic_loader_cache']={'sha256':h,'bytes':n}
    value={'schema_version':'bie.installed-toolchain.v1','package_sha256':file_hash(root/'package.json')[0],
           'lock_sha256':file_hash(root/'package-lock.json')[0],'node_tree':inventory,'installed_packages':installed,
           'absent_optional_packages':missing,'tools':tools,'runtime_resources':runtime_resources,'authenticity':'BYTE_IDENTITY_NOT_PUBLISHER_SIGNATURE',
           'cross_host_reproducibility':'NOT_ESTABLISHED','accepted':False}
    value['identity_sha256']=digest(value)
    return value


def require_same_toolchain(before, after):
    for value in (before,after):
        base={k:v for k,v in value.items() if k!='identity_sha256'}
        if value.get('identity_sha256')!=digest(base):fail('TOOLCHAIN_RECEIPT_TAMPERED','identity')
    if before['identity_sha256']!=after['identity_sha256']:fail('TOOLCHAIN_CHANGED','reinstall/republish and revalidate')
    return True
