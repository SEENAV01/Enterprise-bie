def composition(scene_id,canvas,objects,constraints=None,
                camera=None,safe_area=None):
    return {"scene_id":scene_id,"canvas":canvas,"objects":objects,
            "constraints":constraints or [],
            "camera":camera or {},"safe_area":safe_area}

def camera_spec(mode="STATIC",target=None,framing=None):
    return {"mode":mode,"target":target,"framing":framing}
