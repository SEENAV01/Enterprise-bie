from pathlib import Path
import hashlib
import json
from ..errors import GameContractError
from .pins import VENDOR_MANIFEST_SHA256

def verify_vendor(root=None):
    root = Path(root) if root is not None else Path(__file__).parent / 'vendor'
    raw = (root / 'vendor-manifest.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != VENDOR_MANIFEST_SHA256:
        raise GameContractError('GAME_REACT_VENDOR_MANIFEST_TAMPER')
    manifest = json.loads(raw)
    expected = {'vendor-manifest.json'}
    for row in manifest['files']:
        name = row['path']
        if Path(name).name != name or name in expected:
            raise GameContractError('GAME_REACT_VENDOR_PATH')
        expected.add(name)
        file = root / name
        if file.is_symlink() or not file.is_file():
            raise GameContractError('GAME_REACT_VENDOR_FILE_MISSING', name)
        data = file.read_bytes()
        if len(data) != row['size_bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
            raise GameContractError('GAME_REACT_VENDOR_FILE_TAMPER', name)
    actual = {p.name for p in root.iterdir()}
    if actual != expected:
        raise GameContractError('GAME_REACT_VENDOR_UNTRACKED_FILE')
    return manifest

def materialize_vendor(runtime):
    source = Path(__file__).parent / 'vendor'
    manifest = verify_vendor(source)
    runtime = Path(runtime)
    for name in [x['path'] for x in manifest['files']] + ['vendor-manifest.json']:
        target = runtime / name
        if target.exists() or target.is_symlink():
            raise GameContractError('GAME_REACT_VENDOR_DESTINATION_EXISTS', name)
    for name in [x['path'] for x in manifest['files']] + ['vendor-manifest.json']:
        (runtime / name).write_bytes((source / name).read_bytes())
    return manifest
