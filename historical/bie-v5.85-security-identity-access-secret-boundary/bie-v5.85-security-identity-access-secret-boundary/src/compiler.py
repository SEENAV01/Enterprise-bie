from authorize import decision
from authn import authenticated

def compile_access(context,principal_record,resource,policy):
    if not authenticated(context):
        return {"schema_version":"5.85",
                "decision":{"allowed":False,"reason":"UNAUTHENTICATED"},
                "quality_gate":{"valid":True,"errors":[]}}
    result=decision(context,principal_record,resource,policy)
    return {"schema_version":"5.85","decision":result,
            "quality_gate":{"valid":True,"errors":[]}}
