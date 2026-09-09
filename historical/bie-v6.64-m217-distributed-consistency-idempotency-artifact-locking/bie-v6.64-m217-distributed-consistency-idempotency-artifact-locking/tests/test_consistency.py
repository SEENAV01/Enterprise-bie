import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))

from idempotency import IdempotencyStore
from state_store import VersionedStateStore
from lock import ArtifactLockManager
from fencing import FencingTokens
from write_guard import guarded_write
from reconciliation import reconcile

def test_idempotency():
    s=IdempotencyStore()
    a=s.begin("k","f")
    b=s.begin("k","f")
    assert a is b

def test_state_lock_fencing():
    s=VersionedStateStore()
    r=s.read("x")
    assert s.compare_and_set("x",r["version"],{"ok":True})
    locks=ArtifactLockManager(); assert locks.acquire("a","w")
    f=FencingTokens(); t=f.issue("a")
    assert guarded_write(locks,f,"a","w",t,{"ok":True})["fencing_token"]==t

def test_reconciliation():
    r=reconcile([{"version":2,"value":"x"},{"version":2,"value":"x"}])
    assert r["status"]=="CONSISTENT"
