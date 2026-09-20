from .element_compiler_common import *
def compile_image_or_video_element(element):
    eid,etype,props,acc,src,rsn=normalize_element(element)
    if etype not in {"image","video"}:
        raise ElementCompilerError("expected image or video")
    path=require_resolved_asset(props)
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
