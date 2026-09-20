from .element_compiler_common import *
def compile_image_or_video_element(element, *, presentation=None):
    if presentation is not None:
        return _compile_verified_media(element, presentation)
    eid,etype,props,acc,src,rsn=normalize_element(element)
    if etype not in {"image","video"}:
        raise ElementCompilerError("expected image or video")
    path=require_resolved_asset(props)
    if etype == "image" and "crop" in props:
        raise ElementCompilerError("MEDIA_CROP_BINDING_REQUIRED: use verified media presentation")
    if etype == "video" and (props.get("trim_start_ms", 0) != 0 or props.get("trim_end_ms") is not None):
        raise ElementCompilerError("MEDIA_TRIM_BINDING_REQUIRED: use the source-bound frame contract")
    comp=component_name("Image" if etype=="image" else "Video",eid)
    if etype=="image":
        source=f"""import React from "react";
import {{CanvasImage, staticFile}} from "remotion";

export const {comp}: React.FC = () => {{
  return <CanvasImage src={{staticFile({jsx(path)})}} style={{{{width: "100%", height: "100%"}}}} />;
}};
"""
        deps=()
    else:
        source=f"""import React from "react";
import {{staticFile}} from "remotion";
import {{Video}} from "@remotion/media";

export const {comp}: React.FC = () => {{
  return <Video src={{staticFile({jsx(path)})}} />;
}};
"""
        deps=("@remotion/media",)
    return compile_result(eid,etype,comp,source,dependencies=deps,assets=(path,))


def _compile_verified_media(element, binding):
    eid,etype,props,acc,src,rsn=normalize_element(element)
    if binding["element_id"] != eid or binding["kind"] != etype:
        raise ElementCompilerError("MEDIA_EMITTER_BINDING_MISMATCH")
    path=require_resolved_asset(props);a=binding["asset"];p=binding["presentation"]
    if a["public_path"]!=path:raise ElementCompilerError("MEDIA_EMITTER_ASSET_MISMATCH")
    comp=component_name("Image" if etype=="image" else "Video",eid)
    if etype=="image":
        ow,oh=p["crop_viewport"];ix,iy=p["image_offset"];iw,ih=p["image_size"];ox,oy=p["viewport_offset"]
        viewport={"position":"absolute","left":ox,"top":oy,"width":ow,"height":oh,"overflow":"hidden"}
        image={"position":"absolute","left":ix,"top":iy,"width":iw,"height":ih,"maxWidth":"none","display":"block"}
        source=('import React from "react";\nimport {CanvasImage, staticFile} from "remotion";\n'
                +f'export const {comp}: React.FC = () => {{\n  return <div role="img" aria-label={{{jsx(acc.get("alt") or "Source image")}}} data-bie-media-kind="image" data-bie-media-viewport={{{jsx(eid)}}} data-bie-source-crop={{{jsx(p["source_crop"])}}} style={{{jsx(viewport)}}}>\n'
                +f'    <CanvasImage src={{staticFile({jsx(path)})}} style={{{jsx(image)}}} />\n  </div>;\n}};\n')
        deps=()
    elif etype=="video":
        start=p["display_start_frame"];end=p["display_end_frame_exclusive"];before=p["trim_before_composition_frames"];after=p["trim_after_composition_frames"]
        muted="true" if p["audio_policy"]=="muted" else "false"
        source=('import React from "react";\nimport {Sequence, staticFile, useCurrentFrame} from "remotion";\nimport {Video} from "@remotion/media";\n'
                +f'export const {comp}: React.FC = () => {{\n  const frame=useCurrentFrame();\n  const active=frame >= {start} && frame < {end};\n'
                +f'  return <div data-bie-media-kind="video" data-bie-media-viewport={{{jsx(eid)}}} style={{{{width:"100%",height:"100%",visibility:active?"visible":"hidden"}}}}>\n'
                +f'    <Sequence from={{{start}}} durationInFrames={{{end-start}}} layout="none">\n'
                +f'      <Video src={{staticFile({jsx(path)})}} trimBefore={{{before}}} trimAfter={{{after}}} muted={{{muted}}} volume={{1}} objectFit="contain" onError={{() => "fail"}} style={{{{width:"100%",height:"100%",display:"block"}}}} />\n'
                +'    </Sequence>\n  </div>;\n};\n')
        deps=("@remotion/media",)
    else:raise ElementCompilerError("MEDIA_KIND_UNSUPPORTED")
    return compile_result(eid,etype,comp,source,dependencies=deps,assets=(path,))
