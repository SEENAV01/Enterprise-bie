"""Verify supplemental integrations without executing any archived source."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def audit(root=ROOT):
    root = Path(root)
    errors = []
    archives_checked = members_checked = targets_checked = 0
    sha = lambda data: hashlib.sha256(data).hexdigest()

    def path(value):
        p = PurePosixPath(value)
        if p.is_absolute() or '..' in p.parts or '\\' in value:
            raise ValueError('unsafe manifest path: '+value)
        target = (root / value).resolve()
        if not target.is_relative_to(root.resolve()):
            raise ValueError('manifest target outside repository')
        return target

    manifests = sorted((root / 'manifests').glob('*_integration_*.json'))
    if not manifests:
        errors.append('No supplemental integration manifests found')
    for manifest_path in manifests:
        try:
            m = json.loads(manifest_path.read_text())
            if 'archives' not in m or 'members' not in m:
                raise ValueError('integration manifest lacks archives/members')
            if len(m['archives']) != m['archive_count'] or len(m['members']) != m['member_count']:
                raise ValueError('declared archive/member counts differ')
            names = [a['archive'] for a in m['archives']]
            if len(names) != len(set(names)) or any(x['archive'] not in names for x in m['members']):
                raise ValueError('duplicate or unknown archive record')
            for a in m['archives']:
                try:
                    data = path(a['backup_path']).read_bytes()
                    if sha(data) != a['archive_sha256']:
                        raise ValueError('original ZIP hash mismatch')
                    rows = [x for x in m['members'] if x['archive'] == a['archive']]
                    with zipfile.ZipFile(path(a['backup_path'])) as z:
                        actual = [n for n in z.namelist() if not n.endswith('/')]
                        if Counter(x['member'] for x in rows) != Counter(actual) or len(rows) != a['member_count']:
                            raise ValueError('original member inventory mismatch')
                        if len(actual) != len(set(actual)) or z.testzip() is not None:
                            raise ValueError('duplicate or corrupt ZIP member')
                        for row in rows:
                            original = z.read(row['member'])
                            if sha(original) != row['original_sha256']:
                                raise ValueError('original member hash mismatch: '+row['member'])
                            if row['state'] not in {'MIGRATED','ARCHIVED_EVIDENCE','DUPLICATE_WITH_PROVENANCE','EXCLUDED_WITH_REASON'}:
                                raise ValueError('undocumented disposition')
                            if row['canonical_path']:
                                if sha(path(row['canonical_path']).read_bytes()) != row['canonical_sha256']:
                                    raise ValueError('canonical target hash mismatch: '+row['canonical_path'])
                                targets_checked += 1
                            elif row['state'] not in {'ARCHIVED_EVIDENCE','EXCLUDED_WITH_REASON'} or not row.get('transformation'):
                                raise ValueError('missing canonical target without documented archive disposition')
                            members_checked += 1
                    archives_checked += 1
                except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as exc:
                    errors.append(a.get('archive','unknown')+': '+str(exc))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(manifest_path.name+': '+str(exc))
    return dict(passed=not errors, errors=errors, manifests=len(manifests), archives_checked=archives_checked,
                original_members_checked=members_checked, canonical_targets_checked=targets_checked,
                acceptance='NOT_ACCEPTED', scope='Original ZIP/member preservation and declared canonical hashes')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output', default='validation/ingested_archive_integrity.json')
    args=parser.parse_args()
    report=audit()
    target=Path(args.output)
    if not target.is_absolute(): target=ROOT/target
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
