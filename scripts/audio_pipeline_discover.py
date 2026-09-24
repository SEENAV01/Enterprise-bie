import sys
sys.path.insert(0,'/engine')
from bie.audio.pipeline_discovery import main
try:raise SystemExit(main())
except (ValueError,OSError,RuntimeError,KeyError,TypeError) as exc:
    print(getattr(exc,'code','PIPELINE_DISCOVERY_FAILED'),file=sys.stderr)
    raise SystemExit(2)
