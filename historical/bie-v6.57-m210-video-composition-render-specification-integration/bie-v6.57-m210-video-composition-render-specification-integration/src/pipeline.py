from layer import layer
from composition import composition,valid as composition_valid
from caption import caption,valid as caption_valid
from transition import transition,valid as transition_valid
from render import render_profile,valid as render_valid
from sync import sync_point,valid as sync_valid
from provenance import provenance,traceable
from verification import verification,passed

def build_video_composition():
    layers=[
        layer("l-bg","BACKGROUND","asset://background",0,195,0),
        layer("l-v1","VISUAL","asset://force-diagram",75,50,1),
        layer("l-eq","EQUATION","asset://force-equation",20,55,2),
        layer("l-cap","CAPTION","captions://lesson",0,195,5)
    ]
    comp=composition("composition-1","storyboard-1",layers,
                     1920,1080,30,195,"asset://background")

    caps=[
        caption("cap-1","Electric charge",0,4,
                {"size":"large","position":"center"},"b1"),
        caption("cap-2","Like charges repel; unlike charges attract.",
                75,90,{"size":"medium","position":"bottom"},"b4")
    ]
    trans=[
        transition("t1","FADE",20,0.5,"sc1","sc2"),
        transition("t2","DISSOLVE",75,0.5,"sc2","sc3")
    ]
    syncs=[
        sync_point("sync1","sc2","narr-1",["asset-force-equation"],20,75),
        sync_point("sync2","sc3","narr-2",["asset-force-diagram"],75,125)
    ]
    render=render_profile("render-1080p","MP4","H264",1920,1080,30,
                          "12Mbps","AAC")
    prov=provenance("composition-1",["storyboard-1"],
                    ["asset-force-diagram","asset-force-equation"],
                    ["audio-1"],["sc2","sc3"],
                    ["artifact://asset-manifest"])
    check=verification("verify-render-plan","composition-1","PASS")

    return {
        "schema_version":"6.57","composition":comp,
        "captions":caps,"transitions":trans,"sync_points":syncs,
        "render_profile":render,"provenance":prov,
        "verification":check,
        "quality_gate":{"valid":(
            composition_valid(comp)
            and all(caption_valid(c) for c in caps)
            and all(transition_valid(t) for t in trans)
            and all(sync_valid(s) for s in syncs)
            and render_valid(render) and traceable(prov)
            and passed(check)
        ),"errors":[]}
    }
