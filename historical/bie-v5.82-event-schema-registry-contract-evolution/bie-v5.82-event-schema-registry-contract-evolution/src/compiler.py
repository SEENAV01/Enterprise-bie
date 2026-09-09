from validate import validate_event
from compatibility import compatibility
from evolution import evolution_plan

def compile_schema_change(event_type,current_version,
                          target_version,old_schema,new_schema,
                          sample_event=None):
    comp=compatibility(old_schema,new_schema)
    validation=(validate_event(sample_event,new_schema)
                if sample_event is not None else None)
    plan=evolution_plan(event_type,current_version,
                        target_version,comp)
    errors=[]
    if validation and not validation["valid"]:
        errors.append("SAMPLE_EVENT_INVALID")
    return {"schema_version":"5.82",
            "compatibility":comp,
            "evolution_plan":plan,
            "sample_validation":validation,
            "quality_gate":{"valid":not errors,"errors":errors}}
