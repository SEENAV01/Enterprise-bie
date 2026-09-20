from pathlib import Path

def canonical_archive_path(root: Path, original_path: str) -> Path:
    # Original app/bie/__init__.py is a package marker, not the canonical compatibility loader.
    if original_path == "app/bie/__init__.py":
        return root / "docs/evidence/post-dir-integration/source-metadata/COMP/app/bie/__init__.py"
    return root / (original_path[4:] if original_path.startswith("app/bie/") else original_path)
