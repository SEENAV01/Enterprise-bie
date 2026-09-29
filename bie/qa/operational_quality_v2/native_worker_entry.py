"""Internal trusted adapter. This never accepts an arbitrary import/function name."""
import os,json,sys
from pathlib import Path
r=json.loads((Path(os.environ['BIE_INPUT_ROOT'])/'request.json').read_text())
sys.path.insert(0,r['checkout'])
try:
    from bie.compiler.linux_worker import run_isolated
    p,proof=run_isolated(tuple(r['command']),workspace=r['workspace'],engine=r['checkout'],writable=tuple(r['writable']),timeout_s=r['timeout'])
    result={'outcome':p.outcome,'exit_code':p.process.exit_code,'proof':proof,'error':None}
except Exception as e:
    result={'error':type(e).__name__+':'+str(e)[:2000],'outcome':'BLOCKED'}
(Path(os.environ['BIE_OUTPUT_ROOT'])/'native.json').write_text(json.dumps(result,sort_keys=True))
