"""Report how an npm lock for a Remotion project relates to the Remotion pairing check (Task 037B).

``bie.compiler.installed_toolchain`` requires every lock entry under ``node_modules/@remotion/``
to carry the ``remotion`` version (``TOOLCHAIN_REMOTION_PAIR``). That prefix also matches
non-Remotion packages that npm nests inside a Remotion package directory when a hoisting
conflict appears, for example ``node_modules/@remotion/studio/node_modules/zod``.

This script only reads a ``package-lock.json`` and prints one GitHub annotation saying which
entries the check would reject, split into real ``@remotion/*`` packages and nested foreign
packages. It changes nothing.
"""
from pathlib import Path
import json, sys


def package_name(location):
    return location.rsplit('node_modules/', 1)[-1]


def report(lock):
    packages = lock.get('packages') or {}
    remotion = (packages.get('node_modules/remotion') or {}).get('version')
    rejected = {'remotion_packages': [], 'nested_foreign_packages': []}
    for location, meta in sorted(packages.items()):
        if not location.startswith('node_modules/@remotion/'):
            continue
        version = meta.get('version')
        if version == remotion:
            continue
        name = package_name(location)
        kind = 'remotion_packages' if name == 'remotion' or name.startswith('@remotion/') else 'nested_foreign_packages'
        rejected[kind].append(f'{location}@{version}')
    return {'remotion': remotion, 'pairing_check_passes': not any(rejected.values()), **rejected}


def main(argv):
    if len(argv) != 2:
        print('usage: remotion_tree_report.py LABEL PACKAGE_LOCK', file=sys.stderr)
        return 2
    label, path = argv
    try:
        result = report(json.loads(Path(path).read_text(encoding='utf-8')))
    except (OSError, ValueError) as exc:
        result = {'error': type(exc).__name__}
    level = 'notice' if result.get('pairing_check_passes') else 'warning'
    title = f'Remotion tree {label}'.replace(':', '%3A').replace(',', '%2C')
    print(f'::{level} title={title}::' + json.dumps(result, sort_keys=True)[:3000], flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
