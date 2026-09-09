def next_fencing_token(previous):
    return int(previous)+1

def fencing_check(operation_token,current_token):
    return operation_token >= current_token

def reject_stale(operation_token,current_token):
    return operation_token < current_token
