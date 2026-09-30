"""H4-002: freeze manifest bytes using H3 descriptor confinement, before JS runs."""
from contextlib import contextmanager
from pathlib import Path
import tempfile, os
from ..models import BenchmarkError, digest
from ..adoption.custody import open_root, capture
from .contracts import candidate, BrowserLimits

@contextmanager
def freeze(root,value,limits=BrowserLimits()):
    c=candidate(value,limits)
    with open_root(root) as fd, tempfile.TemporaryDirectory(prefix='bie-browser-assets-') as temp:
        records=[]
        for row in sorted(c['files'],key=lambda x:x['path']):
            p=Path(temp)/row['path'];p.parent.mkdir(parents=True,exist_ok=True)
            with p.open('xb') as out:
                records.append(capture(fd,row,maximum=limits.max_file_bytes,destination=out))
                out.flush();os.fsync(out.fileno())
            p.chmod(0o400)
        yield Path(temp),{'files':records,'sha256':digest(records),'custody':'CONFINED_PRIVATE_SNAPSHOT'}
