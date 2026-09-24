#!/usr/bin/env python3
"""Fixed standalone child launcher; production modules never bootstrap archives."""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def bootstrap():
    sys.path.insert(0,str(ROOT))
    snapshot=ROOT/'dependency_snapshot'
    if snapshot.exists():
        if snapshot.is_symlink() or not snapshot.is_dir():
            raise ValueError('ACOUSTIC_DEPENDENCY_PATH')
        manifest=json.loads((ROOT/'DEPENDENCY_SNAPSHOT.json').read_text())
        for row in manifest['files']:
            name=Path(row['path'])
            if name.is_absolute() or '..' in name.parts:
                raise ValueError('ACOUSTIC_DEPENDENCY_PATH')
            path=snapshot/name
            if path.is_symlink() or not path.is_file():
                raise ValueError('ACOUSTIC_DEPENDENCY_PATH')
            data=path.read_bytes()
            blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
            if (len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']
                    or blob!=row['expected_git_blob']):
                raise ValueError('ACOUSTIC_DEPENDENCY_IDENTITY')
        sys.path.append(str(snapshot))


if __name__=='__main__':
    try:
        bootstrap()
        from bie.audio.acoustic_worker import main
        raise SystemExit(main())
    except (ValueError,OSError,RuntimeError,KeyError,TypeError) as exc:
        print(getattr(exc,'code','ACOUSTIC_NATIVE_LAUNCH_FAILED'),file=sys.stderr)
        raise SystemExit(2)
