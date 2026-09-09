def adapter(adapter_id,backend_ref,operations=None,
           input_mapping=None,output_mapping=None,
           error_mapping=None):
    return {"adapter_id":adapter_id,"backend_ref":backend_ref,
            "operations":operations or [],
            "input_mapping":input_mapping or {},
            "output_mapping":output_mapping or {},
            "error_mapping":error_mapping or {}}

def adapter_operation(name,input_schema=None,output_schema=None):
    return {"name":name,"input_schema":input_schema or {},
            "output_schema":output_schema or {}}
