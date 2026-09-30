"""H4-004: real click/fill/key/reload actions and independently observed states."""
from .observe import observe

def run_steps(page,steps,timeout_ms,*,boot=None):
    records=[]
    for step in steps:
        error=None
        try:
            op=step['action']
            if op=='click':page.locator(step['target']).click(timeout=timeout_ms)
            elif op=='fill':page.locator(step['target']).fill(step['value'],timeout=timeout_ms)
            elif op=='press':page.keyboard.press(step['value'])
            elif op=='reload':
                if boot is None:raise ValueError('trusted local-document reset required')
                boot()
            elif op!='inspect':raise ValueError('unsupported validated action')
            # A frame boundary lets event-driven UI updates settle. Never waits
            # for candidate-declared success or injects expected answers into JS.
            page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => resolve()))')
        except Exception as exc:
            error={'code':'ACTION_EXECUTION_FAILED','exception_type':type(exc).__name__}
        observations={}
        if error is None:
            for check in step['checks']:
                observations[check['target']]=observe(page,check['target'])
        records.append({'step_id':step['id'],'action':step['action'],'action_error':error,'observations':observations})
        if error is not None:break
    return records
