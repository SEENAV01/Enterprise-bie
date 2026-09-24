"""Fixed canonical-worker entry. Never accepts an arbitrary operation or path."""
import sys
sys.path.insert(0,'/engine')
from bie.audio.pipeline_worker import main
try:
    raise SystemExit(main())
except (ValueError,OSError,RuntimeError,KeyError,TypeError) as exc:
    print(getattr(exc,'code','PIPELINE_CHILD_FAILED'),file=sys.stderr)
    raise SystemExit(2)
