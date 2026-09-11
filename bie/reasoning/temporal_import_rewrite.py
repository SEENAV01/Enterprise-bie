from pathlib import Path

def rewrite_temporal_imports(path: str):
    p=Path(path)
    text=p.read_text()
    new=text.replace("from app.bie.", "from bie.").replace("import app.bie.", "import bie.")
    changed=(new!=text)
    if changed:
        p.write_text(new)
    return changed
