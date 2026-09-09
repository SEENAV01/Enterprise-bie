CODES={
"VALIDATION_ERROR":400,
"UNAUTHORIZED":401,
"FORBIDDEN":403,
"NOT_FOUND":404,
"CONFLICT":409,
"RATE_LIMITED":429,
"INTERNAL_ERROR":500
}

def error(code,message,request_id=None,
          correlation_id=None,details=None):
    return {"error":{"code":code,"message":message,
                     "details":details or {}},
            "request_id":request_id,
            "correlation_id":correlation_id}

def status_for(code):
    return CODES.get(code,500)
