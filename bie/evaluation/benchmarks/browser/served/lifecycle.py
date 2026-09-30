"""H5-005: real origin navigation/reload. Never set_content/eval as fallback."""
from time import monotonic,sleep
from ..observe import observe
from ...models import BenchmarkError

def ready(page,policy,timeout_ms):
    end=monotonic()+timeout_ms/1000
    last=None
    while monotonic()<end:
        last=observe(page,policy['target'])
        if last.get('present') and last.get('text')==policy['text'] and last.get('visible'):
            return {'ready':True,'target':policy['target'],'observed_text':last['text']}
        page.wait_for_timeout(20)
    raise BenchmarkError('HTTP_APP_READINESS_TIMEOUT')

def navigate(page,url,policy,timeout_ms,*,reload=False):
    try:
        response=page.reload(wait_until='load',timeout=timeout_ms) if reload else page.goto(url,wait_until='load',timeout=timeout_ms)
    except Exception as exc:
        if 'ERR_BLOCKED_BY_ADMINISTRATOR' in str(exc):raise BenchmarkError('HTTP_NAVIGATION_ADMINISTRATOR_BLOCKED') from exc
        raise BenchmarkError('HTTP_NAVIGATION_FAILED') from exc
    if response is None or response.status!=200 or page.url!=url:
        raise BenchmarkError('HTTP_NAVIGATION_BINDING_FAILED')
    return ready(page,policy,timeout_ms)

def run_steps(page,steps,timeout_ms,*,boot=None):
    """Execute once, then boundedly observe async UI; never repeat an action."""
    from ..actions import run_steps as execute_once
    output=[]
    for step in steps:
        row=execute_once(page,[step],timeout_ms,boot=boot)[0]
        if row['action_error'] is None:
            end=monotonic()+timeout_ms/1000
            while True:
                good=True
                for check in step['checks']:
                    state=row['observations'].get(check['target'],{})
                    actual=state.get(check['property']);expected=check['expected']
                    match=(type(actual) in (int,float) and actual>=expected) if check['property']=='contrast_at_least' else (type(actual) is type(expected) and actual==expected)
                    if not state.get('present') or not match:good=False
                if good or monotonic()>=end:break
                page.wait_for_timeout(20)
                row['observations']={check['target']:observe(page,check['target']) for check in step['checks']}
        output.append(row)
        if row['action_error'] is not None:break
    return output
