"""Demonstrate actual native secure-I/O refusal, never patch POSIX guards."""
from pathlib import Path
import json,os,sys,tempfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from bie.qa.release_v2.artifacts import ArtifactStore
from bie.qa.release_v2.contracts import ContractError
with tempfile.TemporaryDirectory(prefix='bie-s18-quality-probe-') as root:
    try:
        with ArtifactStore(root):status='SUPPORTED';code=None
    except ContractError as e:status='NOT_RUN';code=e.code
receipt=dict(platform=os.name,gate_secure_artifact_io=status,diagnostic=code,
    repair_journal_required_no_follow_available=hasattr(os,'O_NOFOLLOW'),guards_modified=False,guard_bypassed=False,
    native_gate_acceptance_claimed=False,task028='PAUSED')
output=Path(sys.argv[1]);output.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
