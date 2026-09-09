import json
from bie_core.build import run

ctx = run()
print(json.dumps({
    "run_id": ctx.run_id,
    "events": ctx.events,
    "artifacts": ctx.artifacts,
    "errors": ctx.errors
}, indent=2))
