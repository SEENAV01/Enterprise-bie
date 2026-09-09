def register_model(store, model_id, version, capabilities, provider, cost_per_unit=0.0):
    key=f"{model_id}:{version}"
    store[key]={"model_id":model_id,"version":version,"capabilities":list(capabilities),
                "provider":provider,"cost_per_unit":cost_per_unit,"status":"ACTIVE"}
    return store[key]

def deactivate_model(store, model_id, version):
    key=f"{model_id}:{version}"
    if key in store: store[key]["status"]="INACTIVE"
    return store.get(key)
