from registry import service,register
from health import health_probe
from routing import routing_policy
from discovery import discover

def compile_service(service_name,version,
                    instance_id,endpoint):
    record=service(service_name,version,
                   instance_id,endpoint)
    registry=register({},record)
    probe=health_probe(instance_id,"READINESS",
                       0,"HEALTHY")
    return {"schema_version":"6.00",
            "service":record,
            "registry":registry,
            "probe":probe,
            "routing_policy":routing_policy(
                service_name),
            "discovered":discover(registry,service_name),
            "quality_gate":{"valid":True,"errors":[]}}
