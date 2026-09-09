def secret_ref(name,provider="SECRET_STORE",
               version=None):
    return {"name":name,"provider":provider,
            "version":version,"kind":"SECRET_REFERENCE"}

def is_reference(record):
    return record["kind"]=="SECRET_REFERENCE"
