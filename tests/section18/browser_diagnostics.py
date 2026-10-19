"""Safe failure evidence for the native browser journeys (Task 037B, F-08)."""
import json,re

SAFE_DIAGNOSTIC=('rootResponse','domReady','loadSeen','healthStatus','childExited','contexts','sessions',
    'requestSent','frameLoading','socketState','socketClose','targetListed')
def failure_annotation(scenario,mode,stderr):
    """Task 037B (F-08): CI job logs are not always downloadable, so a failed journey
    is also surfaced as a run annotation. Whitelisted codes and bool/int/null
    diagnostic fields only; never raw child output, expressions or credentials."""
    codes=re.findall(r'NATIVE_UI_FAILED:([A-Z_]+(?::[A-Z][A-Za-z.]+:\d+)?)',stderr)
    diagnostic={}
    for line in stderr.splitlines():
        if line.startswith('NATIVE_CDP_DIAGNOSTIC:'):
            try:raw=json.loads(line.split(':',1)[1])
            except ValueError:continue
            if isinstance(raw,dict):
                diagnostic={k:raw[k] for k in SAFE_DIAGNOSTIC if k in raw and (raw[k] is None or type(raw[k]) in (bool,int))}
    return '::warning title=Section 18 browser failure::'+json.dumps(
        dict(scenario=scenario,mode=mode,codes=codes[:3],diagnostic=diagnostic),sort_keys=True)
