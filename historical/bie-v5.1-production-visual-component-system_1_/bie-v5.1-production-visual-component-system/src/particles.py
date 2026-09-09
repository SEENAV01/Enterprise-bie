def particle_spec(count, path, speed=1.0, seed=0, purpose="flow"):
    return {
      "type":"PARTICLES",
      "count":count,
      "path":path,
      "speed":speed,
      "seed":seed,
      "purpose":purpose,
      "deterministic":True
    }
