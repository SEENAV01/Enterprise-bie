def physical_law(law_id,name,equation,variables,domain,
                 conservation=None):
    return {
      "law_id":law_id,"name":name,"equation":equation,
      "variables":variables,"domain":domain,
      "conservation":conservation
    }

def conservation_rule(rule_id,quantity,initial,final,tolerance=1e-9):
    return {
      "rule_id":rule_id,"quantity":quantity,
      "initial":initial,"final":final,"tolerance":tolerance
    }
