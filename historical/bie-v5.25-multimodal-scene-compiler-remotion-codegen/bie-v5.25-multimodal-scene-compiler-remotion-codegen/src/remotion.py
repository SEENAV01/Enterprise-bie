def remotion_component(name,imports=None,body=None):
    return {"name":name,"imports":imports or [],
            "body":body or ""}

def composition_spec(composition_id,component,duration_frames,
                     fps,width=1920,height=1080):
    return {"id":composition_id,"component":component,
            "durationInFrames":duration_frames,"fps":fps,
            "width":width,"height":height}

def generate_component_source(spec):
    imports="\n".join(f"import {x};" for x in spec.get("imports",[]))
    return imports+"\n\n"+spec["body"]
