from idempotency import IdempotencyStore
from state_store import VersionedStateStore
from lock import ArtifactLockManager
from lease import lease,valid as lease_valid
from fencing import FencingTokens
from write_guard import guarded_write
from reconciliation import reconcile
from commit import commit_record,valid as commit_valid

def build_consistency_runtime():
    idem=IdempotencyStore()
    state=VersionedStateStore()
    locks=ArtifactLockManager()
    fencing=FencingTokens()

    key="render:lesson-2:v2"
    first=idem.begin(key,"fingerprint-v2")
    duplicate=idem.begin(key,"fingerprint-v2")

    artifact_id="artifact://lesson-2.mp4"
    owner="worker-1"
    assert locks.acquire(artifact_id,owner)
    token=fencing.issue(artifact_id)
    guarded=guarded_write(
        locks,fencing,artifact_id,owner,token,
        {"status":"RENDERED","uri":artifact_id}
    )

    lease_record=lease("lease-1",artifact_id,owner,"future")
    initial=state.read("lesson-2")
    cas_ok=state.compare_and_set(
        "lesson-2",initial["version"],
        {"state":"RENDERED","artifact":artifact_id}
    )
    idem.complete(key,{"artifact":artifact_id})

    consistent=reconcile([
        {"version":1,"value":{"state":"RENDERED"}},
        {"version":1,"value":{"state":"RENDERED"}}
    ])

    commit=commit_record(
        "commit-1",artifact_id,owner,key,token,"sha256:demo"
    )
    released=locks.release(artifact_id,owner)

    return {
        "schema_version":"6.64",
        "idempotency":{"first":first,"duplicate":duplicate,
                       "final":idem.get(key)},
        "versioned_state":{"read_initial":initial,
                           "compare_and_set":cas_ok,
                           "current":state.read("lesson-2")},
        "artifact_lock":{"acquired":True,"released":released,
                         "owner_after_release":locks.owner(artifact_id)},
        "fencing_token":token,
        "guarded_write":guarded,
        "lease":lease_record,
        "reconciliation":consistent,
        "commit":commit,
        "consistency_gate":{"valid":(
            first is duplicate
            and idem.get(key)["status"]=="COMPLETED"
            and cas_ok
            and guarded["fencing_token"]==token
            and lease_valid(lease_record)
            and consistent["status"]=="CONSISTENT"
            and commit_valid(commit)
            and released
        ),"errors":[]}
    }
