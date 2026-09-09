def trust_policy():
    return {
      "UNTRUSTED":{"allowed_outbound":["SANDBOX"]},
      "SANDBOX":{"allowed_outbound":["WORKER"]},
      "WORKER":{"allowed_outbound":["PRODUCTION"]},
      "PRODUCTION":{"allowed_outbound":["PROTECTED"]},
      "PROTECTED":{"allowed_outbound":[]}
    }

def security_policy():
    return {
      "model_output_is_untrusted_by_default":True,
      "credentials_are_scoped":True,
      "secrets_are_referenced_not_embedded":True,
      "trust_crossings_are_explicit":True,
      "rotation_is_recorded":True,
      "privileged_execution_requires_explicit_boundary":True
    }
