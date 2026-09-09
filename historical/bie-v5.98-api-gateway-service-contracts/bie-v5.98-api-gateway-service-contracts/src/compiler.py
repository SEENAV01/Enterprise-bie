from gateway import route
from contract import service_contract
from versioning import api_version

def compile_api(name,version,method,path,service,
                request_schema,response_schema,
                auth_scope=None):
    r=route(method,path,service,auth_scope,version)
    c=service_contract(name,version,
                       request_schema,response_schema)
    return {"schema_version":"5.98",
            "version":api_version(version),
            "route":r,"contract":c,
            "quality_gate":{"valid":True,"errors":[]}}
