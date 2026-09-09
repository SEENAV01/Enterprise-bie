def pace(masteries,base_minutes=20):
    avg=sum(masteries.values())/len(masteries) if masteries else 0
    factor=1.25 if avg<0.6 else (1.0 if avg<0.85 else 0.8)
    return {"base_minutes":base_minutes,"factor":factor,
            "recommended_minutes":round(base_minutes*factor,2)}
