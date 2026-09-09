def resource_request(complexity,quality):
    level=complexity["level"]
    base={"LOW":{"cpu":1,"memory":2,"gpu":0},
          "MEDIUM":{"cpu":2,"memory":4,"gpu":0},
          "HIGH":{"cpu":4,"memory":8,"gpu":1},
          "EXTREME":{"cpu":8,"memory":16,"gpu":2}}[level].copy()
    if quality.get("visual")=="HIGH":
        base["gpu"]=max(base["gpu"],1 if level!="LOW" else 0)
    return base
