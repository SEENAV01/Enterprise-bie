def authorization_audit(decision_id,
                        subject,tenant,action,
                        resource,decision,
                        policy_version,timestamp,
                        reason=None):
    return {"decision_id":decision_id,
            "subject":subject,"tenant":tenant,
            "action":action,"resource":resource,
            "decision":decision,
            "policy_version":policy_version,
            "timestamp":timestamp,
            "reason":reason}
