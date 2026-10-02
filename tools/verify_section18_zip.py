"""Fail-closed extraction and complete payload checksums; no blind overlay."""
from pathlib import Path,PurePosixPath
import argparse,hashlib,json,re,zipfile

def verify(zip_path,target):
    target=Path(target).absolute();assert not target.exists(),'EXTRACT_TARGET_ALREADY_EXISTS'
    with zipfile.ZipFile(zip_path) as z:
        rows=z.infolist();names=[r.filename for r in rows]
        assert len(names)==len(set(names)) and len(names)<=10000,'DUPLICATE_OR_TOO_MANY_MEMBERS'
        assert sum(r.file_size for r in rows)<=128*1024*1024,'ARCHIVE_SIZE_LIMIT'
        for row in rows:
            path=PurePosixPath(row.filename)
            assert not path.is_absolute() and '..' not in path.parts and '\\' not in row.filename and ':' not in row.filename
            assert all(p not in ('','.') and not p.endswith((' ','.')) and
                not re.fullmatch(r'(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?',p,re.I) for p in path.parts)
            assert (row.external_attr>>16)&0o170000 != 0o120000,'ZIP_LINK'
        manifest=json.loads(z.read('MANIFEST.json'));expected={r['path']:r for r in manifest['files']}
        assert set(expected)==set(names)-{'MANIFEST.json','SHA256SUMS.txt'},'MANIFEST_MEMBER_MISMATCH'
        checks={}
        for line in z.read('SHA256SUMS.txt').decode().splitlines():
            sha,name=line.split('  ',1);assert name not in checks;checks[name]=sha
        assert set(checks)==set(names)-{'SHA256SUMS.txt'},'CHECKSUM_MEMBER_MISMATCH'
        for name,sha in checks.items():
            raw=z.read(name);assert hashlib.sha256(raw).hexdigest()==sha,'CHECKSUM_FAILED:'+name
            if name in expected:assert len(raw)==expected[name]['bytes'] and sha==expected[name]['sha256']
        z.extractall(target)
    return dict(archive=Path(zip_path).name,sha256=hashlib.sha256(Path(zip_path).read_bytes()).hexdigest(),
                members=len(names),checksums_passed=True,extraction_safe=True,extracted_payload_bytes=sum(r.file_size for r in rows))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('zip',type=Path);p.add_argument('target',type=Path);a=p.parse_args()
    print(json.dumps(verify(a.zip,a.target),sort_keys=True))
