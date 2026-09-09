def backend(backend_id,backend_class,capabilities=None,
            versions=None,resource_profile=None):
    return {"backend_id":backend_id,"backend_class":backend_class,
            "capabilities":capabilities or [],
            "versions":versions or [],
            "resource_profile":resource_profile or {}}

def backend_capabilities():
    return ["2D_VECTOR","2D_ANIMATION","3D","VIDEO","AUDIO",
            "INTERACTIVE","SIMULATION","DOCUMENT","GPU_COMPUTE",
            "RASTER","TEXT"]
