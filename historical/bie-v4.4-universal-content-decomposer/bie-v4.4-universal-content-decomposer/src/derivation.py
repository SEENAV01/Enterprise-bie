def derivation_chain(steps):
    return {
      "type":"DERIVATION",
      "steps":[
        {"step":i+1,"statement":s,"depends_on":[i] if i else []}
        for i,s in enumerate(steps)
      ]
    }
