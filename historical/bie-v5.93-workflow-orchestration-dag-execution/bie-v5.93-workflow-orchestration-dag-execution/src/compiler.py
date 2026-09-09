from dag import dag,ready_nodes
from execution import execution
from scheduler import schedule

def compile_workflow(workflow_id,nodes,edges,
                     concurrency=1):
    g=dag(workflow_id,nodes,edges)
    ready=ready_nodes(g,[])
    plan=schedule(workflow_id,ready,concurrency)
    return {"schema_version":"5.93",
            "dag":g,"initial_ready":ready,
            "schedule":plan,
            "execution":execution(workflow_id,"PLANNED"),
            "quality_gate":{"valid":True,"errors":[]}}
