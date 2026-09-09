def sla_status(created_at,now,sla_seconds):
    elapsed=now-created_at
    return {"elapsed":elapsed,
            "sla_seconds":sla_seconds,
            "breached":elapsed>sla_seconds}

def priority_for_sla(breached,priority):
    return max(priority,100) if breached else priority
