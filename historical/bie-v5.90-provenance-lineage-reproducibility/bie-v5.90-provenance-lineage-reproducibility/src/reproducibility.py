from hashing import sha256

def reproduction_fingerprint(model,prompt,config,code,
                             dependencies,environment):
    return sha256({
      "model":model,"prompt":prompt,"config":config,
      "code":code,"dependencies":dependencies,
      "environment":environment
    })

def compare_fingerprint(expected,actual):
    return {"match":expected==actual,
            "expected":expected,"actual":actual}
