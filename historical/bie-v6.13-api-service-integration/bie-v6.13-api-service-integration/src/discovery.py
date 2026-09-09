def service_endpoint(service,
                    address,port,
                    protocol="HTTP"):
    return {"service":service,
            "address":address,
            "port":port,
            "protocol":protocol}

def endpoint_key(record):
    return (record["service"],
            record["address"],record["port"])
