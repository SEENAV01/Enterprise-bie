"""Verify exact supplied inputs and the adopted source ledger (not product QA)."""
from pathlib import Path, PurePosixPath
from hashlib import sha256
import argparse, ast, io, json, stat, zipfile
ROOT = Path(__file__).resolve().parents[1]

def digest(data): return sha256(data).hexdigest()

def safe_file(root, name):
    if not isinstance(name, str) or not name or '\\' in name or '\0' in name:
        raise ValueError('BAD_PATH')
    q = PurePosixPath(name)
    if q.is_absolute() or '..' in q.parts: raise ValueError('UNSAFE_PATH:' + name)
    p = root / name
    if p.is_symlink() or any(x.is_symlink() for x in p.parents) or not p.is_file():
        raise ValueError('FILE_UNAVAILABLE:' + name)
    if not p.resolve().is_relative_to(root.resolve()): raise ValueError('PATH_ESCAPE')
    return p

def verify(root=ROOT, *, recursive=True):
    source = json.loads((root / 'manifests/post_dir_integration_004.json').read_text())
    supplied = json.loads((root / 'manifests/post_dir_supplied_inputs.json').read_text())
    errors = []; checked = {}; archives = {}; nested = []
    def check_file(path, expected, expected_size=None):
        try:
            p = safe_file(root, path)
            if path not in checked:
                data = p.read_bytes(); checked[path] = (digest(data), len(data))
            actual, size = checked[path]
            if actual != expected or expected_size is not None and size != expected_size:
                raise ValueError('HASH_OR_SIZE_MISMATCH:' + path)
        except (OSError, ValueError) as exc: errors.append(str(exc))
    def visit(data, depth=0):
        if depth > 30: raise ValueError('ARCHIVE_DEPTH')
        key = digest(data)
        if key in archives or not data.startswith(b'PK\x03\x04'): return
        archives[key] = True
        if len(archives) > 2000: raise ValueError('ARCHIVE_COUNT')
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            seen = set()
            for m in z.infolist():
                p = PurePosixPath(m.filename)
                if m.filename in seen or p.is_absolute() or '..' in p.parts or '\\' in m.filename:
                    raise ValueError('UNSAFE_ARCHIVE_MEMBER')
                seen.add(m.filename)
                mode = m.external_attr >> 16
                if stat.S_ISLNK(mode): raise ValueError('ARCHIVE_LINK')
                if m.file_size > 100 * 1024 * 1024: raise ValueError('MEMBER_BUDGET')
                b = z.read(m)  # ZIP CRC checked by the library.
                nested.append([key, m.filename, digest(b), len(b)])
                if b.startswith(b'PK\x03\x04'): visit(b, depth+1)
    for item in supplied['files']:
        check_file(item['repository_path'], item['sha256'], item['bytes'])
        if recursive:
            try: visit(safe_file(root, item['repository_path']).read_bytes())
            except (OSError, ValueError, zipfile.BadZipFile) as exc: errors.append(str(exc))
    for item in source['source_members']:
        check_file(item['canonical_path'], item['canonical_sha256'])
    if recursive:
        declared=json.loads((root/'manifests/post_dir_nested_members.json').read_text())['records']
        if sorted(nested) != sorted(declared): errors.append('NESTED_MEMBER_LEDGER_MISMATCH')
    # Fail if production code imports immutable archived packages.
    for folder in ('visual_intelligence', 'animation_intelligence', 'scene_ir', 'compiler'):
        for p in (root/'bie'/folder).rglob('*.py'):
            try:
                tree=ast.parse(p.read_text())
                for n in ast.walk(tree):
                    names=[n.module or ''] if isinstance(n,ast.ImportFrom) else [a.name for a in n.names] if isinstance(n,ast.Import) else []
                    for name in names:
                        if name.startswith(('app.bie','backups.','historical.','batches.')):
                            errors.append('NONCANONICAL_RUNTIME_IMPORT:'+str(p.relative_to(root)))
            except (SyntaxError, UnicodeDecodeError) as exc: errors.append(str(exc))
    return {'passed':not errors, 'errors':sorted(set(errors)), 'supplied_files_verified':len(supplied['files']),
            'source_member_mappings_verified':len(source['source_members']), 'unique_paths_hashed':len(checked),
            'unique_zip_archives_verified':len(archives), 'nested_member_occurrences_verified':len(nested),
            'unavailable_previously_declared_archives':supplied['unavailable_declared_archives'],
            'scope':'All supplied bytes and canonical adoption; no whole-product or real-render acceptance.',
            'accepted':False, 'historical_corpus_completeness':'NOT_CLAIMED'}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
    result=verify()
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['passed'] else 1)
if __name__=='__main__': main()
