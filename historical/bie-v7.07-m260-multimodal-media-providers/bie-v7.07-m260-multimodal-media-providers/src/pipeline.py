from providers import register_provider,select_provider
from generation import create_generation_request,accept_generation
from tts import create_tts_request,accept_tts
from captions import align_captions,validate_captions
from quality import quality_gate,provider_fallback

def build_m260_runtime():
    providers={}
    register_provider(providers,"image-primary","image",["generate"],100)
    register_provider(providers,"image-fallback","image",["generate"],50)
    register_provider(providers,"diagram-primary","diagram",["generate"],100)
    register_provider(providers,"tts-primary","tts",["synthesize"],100)
    register_provider(providers,"tts-fallback","tts",["synthesize"],50)

    image_provider=select_provider(providers,"image","generate")
    image_req=create_generation_request("image-field","image","Electric field around a point charge",
                                        {"resolution":"1920x1080"})
    image=accept_generation(image_req,image_provider["id"],"media/image-field.png",
                            {"resolution":"1920x1080"})

    tts_provider=select_provider(providers,"tts","synthesize")
    tts_req=create_tts_request("narration-1","Electric field is a vector field.","en-IN","educator")
    tts=accept_tts(tts_req,"media/narration-1.wav",3.2)

    words=[{"text":"Electric","start":0.0,"end":0.5},
           {"text":"field","start":0.5,"end":1.0},
           {"text":"is","start":1.0,"end":1.2},
           {"text":"a","start":1.2,"end":1.3},
           {"text":"vector","start":1.3,"end":1.8},
           {"text":"field.","start":1.8,"end":2.3}]
    captions=align_captions(words)
    caption_check=validate_captions(captions,3.2)

    image_quality=quality_gate(image,{"media_kind":"image",
                                      "metadata":{"resolution":"1920x1080"}})
    fallback=provider_fallback(providers,"image","generate","image-primary")
    valid=image_quality["valid"] and caption_check["valid"] and fallback is not None
    return {"schema_version":"7.07","providers":providers,"image":image,
            "image_provider":image_provider,"tts":tts,"tts_provider":tts_provider,
            "captions":captions,"caption_validation":caption_check,
            "image_quality_gate":image_quality,"fallback_provider":fallback,
            "media_generation_gate":{"valid":valid,
                                     "errors":[] if valid else ["MEDIA_GENERATION_FAILURE"]}}
