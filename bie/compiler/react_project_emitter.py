from __future__ import annotations
import json
from .react_emitter_common import *

def emit_react_project(*, project_name, remotion_version, react_version, typescript_version, extra_dependencies=None):
    project_name=nonblank(project_name,"project_name")
    versions={
      "remotion":nonblank(remotion_version,"remotion_version"),
      "react":nonblank(react_version,"react_version"),
      "typescript":nonblank(typescript_version,"typescript_version"),
    }
    deps={
      "remotion":versions["remotion"],
      "react":versions["react"],
      "react-dom":versions["react"],
    }
    dev={
      "@remotion/cli":versions["remotion"],
      "@types/react":"^19.0.0",
      "@types/react-dom":"^19.0.0",
      "typescript":versions["typescript"],
    }
    for k,v in sorted((extra_dependencies or {}).items()):
        if k in deps or k in dev:
            raise ReactEmitterError("extra dependency conflicts with governed dependency: "+k)
        deps[nonblank(k,"dependency")]=nonblank(v,"dependency version")

    package={
      "name":project_name,
      "private":True,
      "version":"0.0.0",
      "scripts":{
        "studio":"remotion studio --no-open",
        "build":"tsc --noEmit",
        "render":"remotion render",
      },
      "dependencies":dict(sorted(deps.items())),
      "devDependencies":dict(sorted(dev.items())),
    }
    tsconfig={
      "compilerOptions":{
        "target":"ES2022","lib":["DOM","DOM.Iterable","ES2022"],"allowJs":False,
        "skipLibCheck":True,"strict":True,"noEmit":True,"esModuleInterop":True,
        "module":"ESNext","moduleResolution":"Bundler","resolveJsonModule":True,
        "isolatedModules":True,"jsx":"react-jsx"
      },
      "include":["src/**/*.ts","src/**/*.tsx","remotion.config.ts"]
    }
    remotion_cfg='import {Config} from "@remotion/cli/config";\n\nConfig.setPixelFormat("yuv420p");\n'
    index='import {registerRoot} from "remotion";\nimport {RemotionRoot} from "./Root";\n\nregisterRoot(RemotionRoot);\n'
    files=(
      emitted_file("package.json",json.dumps(package,indent=2,sort_keys=True)+"\n"),
      emitted_file("tsconfig.json",json.dumps(tsconfig,indent=2,sort_keys=True)+"\n"),
      emitted_file("remotion.config.ts",remotion_cfg),
      emitted_file("src/index.ts",index),
    )
    return tuple(sorted(files,key=lambda f:f.path))
