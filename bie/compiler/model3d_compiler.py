from .element_compiler_common import *
def compile_model3d_element(element):
    eid,props,acc,src,rsn=require_type(element,"model3d")
    path=require_resolved_asset(props)
    comp=component_name("Model3D",eid)
    source=f"""import React from "react";
import {{Canvas}} from "@react-three/fiber";
import {{useGLTF}} from "@react-three/drei";
import {{staticFile}} from "remotion";

const Model = () => {{
  const gltf = useGLTF(staticFile({jsx(path)}));
  return <primitive object={{gltf.scene}} />;
}};

export const {comp}: React.FC = () => {{
  return (
    <Canvas aria-label={{{jsx(acc.get("alt") or "3D model")}}}>
      <ambientLight intensity={{1}} />
      <Model />
    </Canvas>
  );
}};
"""
    return compile_result(eid,"model3d",comp,source,
        dependencies=("@react-three/fiber","@react-three/drei","three"),
        assets=(path,))
