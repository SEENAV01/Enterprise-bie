from pathlib import Path

def audit_temporal_package(root: str, expected_modules):
    root=Path(root)
    canonical=root/"bie"/"reasoning"
    legacy=root/"app"/"bie"/"reasoning"
    exp=tuple(sorted(set(expected_modules)))
    missing=[]
    misplaced=[]
    for name in exp:
        if (canonical/name).exists():
            continue
        if (legacy/name).exists():
            misplaced.append(name)
        else:
            missing.append(name)
    return {
        "expected":len(exp),
        "missing":tuple(missing),
        "misplaced":tuple(misplaced),
        "ready":not missing and not misplaced,
    }
