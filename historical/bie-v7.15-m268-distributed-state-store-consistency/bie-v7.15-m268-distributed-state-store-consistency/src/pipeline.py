from store import StateStore
from checkpoints import create_checkpoint,latest_checkpoint
from consistency import consistency_check,merge_state
from recovery import recover_from_checkpoint,replay_events
from versioning import make_revision,compare_revision

def build_m268_runtime():
    store=StateStore()
    first=store.write("run-001",{"state":"RUNNING"})
    conflict=store.write("run-001",{"state":"PAUSED"},expected_version=0)
    second=store.write("run-001",{"state":"PAUSED"},expected_version=first["version"])

    checkpoints=[
        create_checkpoint("run-001",1,{"state":"RUNNING"}),
        create_checkpoint("run-001",2,{"state":"PAUSED"})
    ]
    latest=latest_checkpoint(checkpoints,"run-001")
    recovery=recover_from_checkpoint(latest)
    events=[{"sequence":1,"type":"START"},{"sequence":2,"type":"PAUSE"},
            {"sequence":3,"type":"RESUME"}]
    replay=replay_events(events,2)

    local={"run":{"version":2,"value":{"state":"PAUSED"}}}
    remote={"run":{"version":3,"value":{"state":"RESUMED"}}}
    merged=merge_state(local,remote)
    consistency=consistency_check({"run":[1,2,3]})
    revision=compare_revision(make_revision("run",2,local["run"]["value"]),
                              make_revision("run",3,remote["run"]["value"]))
    return {"schema_version":"7.15","writes":{"first":first,"conflict":conflict,"second":second},
            "latest_checkpoint":latest,"recovery":recovery,"replay":replay,
            "merge":merged,"consistency":consistency,"revision_comparison":revision,
            "state_store_gate":{"valid":first["ok"] and not conflict["ok"] and second["ok"]
                                and recovery["ok"] and consistency["consistent"],
                                "errors":[]}}
