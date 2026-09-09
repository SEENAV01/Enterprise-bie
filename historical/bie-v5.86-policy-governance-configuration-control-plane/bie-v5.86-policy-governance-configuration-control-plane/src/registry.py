def register(registry,policy_id,version,document,
             environment="base",status="DRAFT"):
    registry.setdefault(policy_id,{})[version]={
        "policy_id":policy_id,"version":version,
        "environment":environment,"status":status,
        "document":document}
    return registry[policy_id][version]

def get(registry,policy_id,version):
    return registry.get(policy_id,{}).get(version)
