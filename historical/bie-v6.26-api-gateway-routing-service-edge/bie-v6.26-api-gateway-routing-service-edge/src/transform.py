def transform(name,
              request_headers=None,
              response_headers=None,
              body=None):
    return {"name":name,
            "request_headers":request_headers or {},
            "response_headers":response_headers or {},
            "body":body}

def header_present(record,name):
    return name in record["request_headers"] or name in record["response_headers"]
