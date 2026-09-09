import json,sys
from pathlib import Path
pages=json.loads(Path(sys.argv[1]).read_text())
out=[{"evidence_id":f"P{p['page']}","page":p["page"],"text":p["text"]} for p in pages if p.get("text","").strip()]
Path(sys.argv[2]).write_text(json.dumps(out,indent=2,ensure_ascii=False))
