"""Verify recovered ZIPs and source copies against the recorded SHA-256 inventory."""
from pathlib import Path
import hashlib, json, zipfile

ROOT = Path(__file__).resolve().parents[1]

def main():
    manifest = json.loads((ROOT/'manifests/archive_inventory.json').read_text())
    files = json.loads((ROOT/'manifests/file_inventory.json').read_text())['files']
    backup = json.loads((ROOT/'manifests/original_backup.json').read_text())
    digest = lambda b: hashlib.sha256(b).hexdigest()
    errors = []
    backup_path = ROOT/backup['path']
    if digest(backup_path.read_bytes()) != backup['sha256']:
        errors.append('Original backup archive checksum mismatch')
    with zipfile.ZipFile(backup_path) as z:
        if len(z.namelist()) != manifest['archive_count']:
            errors.append('Original ZIP count mismatch')
        for a in manifest['archives']:
            if digest(z.read('original-zips/'+a['name'])) != a['sha256']:
                errors.append('Original ZIP mismatch: '+a['name'])
    for f in files:
        p=f['source_path']
        if p is not None:
            if not (ROOT/p).is_file() or digest((ROOT/p).read_bytes()) != f['sha256']:
                errors.append('Imported source mismatch: '+p)
    result={'archive_count':manifest['archive_count'],'imported_member_count':len(files),
            'expanded_files_checked':sum(f['source_path'] is not None for f in files),
            'passed':not errors,'errors':errors}
    print(json.dumps(result,indent=2))
    return 0 if not errors else 1

if __name__=='__main__':
    raise SystemExit(main())
