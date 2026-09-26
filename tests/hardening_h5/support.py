from __future__ import annotations
from pathlib import Path
from tempfile import TemporaryDirectory
from bie.bie_core.artifact_contracts import RunContext
from bie.game_engine.build_runtime_engine.fixtures import build_inputs
from bie.game_engine.operations_engine.contracts import TelemetryConsent,SessionOutcome,EnterpriseSessionRequest

def context_assets():return build_inputs()
def run_context(n=55):return RunContext(f'00000000-0000-4000-8000-{n:012d}','BIE-GAME','1.0.0',['source:book'],'0'*64,'policy:game:h5','env:test','2026-09-25T00:00:00Z')
def request(n=55,*,consent=True,key=None,owner='worker:h5',learner='a'*64,outcome='applied'):
 return EnterpriseSessionRequest(run_context(n),f'session:h5:{n}',learner,key or f'idem:h5:{n}',owner,TelemetryConsent(consent,'policy:telemetry:v1',30),(SessionOutcome('obj:motion','challenge:motion','mechanic_completed',outcome,'drag_and_drop',1,1.0,.9,('adapt:sample',)),))
