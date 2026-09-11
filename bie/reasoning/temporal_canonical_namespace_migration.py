from pathlib import Path
import shutil

def migrate_temporal_module_tree(staging_root: str):
    root=Path(staging_root)
    src=root/"app"/"bie"/"reasoning"
    dst=root/"bie"/"reasoning"
    if not src.exists():
        raise FileNotFoundError("staged app/bie/reasoning tree missing")
    dst.mkdir(parents=True, exist_ok=True)
    copied=[]
    for f in sorted(src.glob("*.py")):
        if f.name=="__init__.py":
            continue
        target=dst/f.name
        shutil.copy2(f,target)
        copied.append(str(target.relative_to(root)))
    return tuple(copied)
