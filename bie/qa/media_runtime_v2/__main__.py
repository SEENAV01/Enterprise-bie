"""Read-only audit; explicit output files must be new. No native execution via JSON."""
from pathlib import Path
from dataclasses import asdict
import argparse,json,sys
from .common import *
from .codec import load_policy,load_request,load_native_profile

def read(p):
    from .storage import open_confined
    import os
    fd=open_confined(p.parent,p.name)
    with os.fdopen(fd,'rb') as f:
        data=f.read(4*1024**2+1)
    require(len(data)<=4*1024**2,'H5_CLI_INPUT_BUDGET');return data

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=('stream','motion','native-preflight'))
    ap.add_argument('--root',type=Path,required=True);ap.add_argument('--policy',type=Path,required=True)
    ap.add_argument('--request',type=Path);ap.add_argument('--tools',type=Path);ap.add_argument('--output',type=Path)
    a=ap.parse_args()
    try:
        if a.output is not None:require(not a.output.exists() and not a.output.is_symlink(),'H5_OUTPUT_EXISTS')
        if a.mode=='native-preflight':
            require(a.request is None and a.tools is None,'H5_PREFLIGHT_UNUSED_INPUTS')
            from .native import preflight
            result=preflight(a.root,load_native_profile(read(a.policy)));status=result['status']
        else:
            require(a.request is not None,'H5_REQUEST_REQUIRED');policy=load_policy(a.mode,read(a.policy));binding,artifact=load_request(read(a.request),a.mode)
            if a.mode=='stream':
                require(a.tools is not None,'H5_OPERATOR_TOOLS_REQUIRED');tools=strict_json(read(a.tools));fields(tools,('ffmpeg','ffprobe'),'H5_TOOL_FIELDS')
                from .stream import inspect
                result=inspect(a.root,artifact,binding,policy,ffmpeg=Tool(**tools['ffmpeg']),ffprobe=Tool(**tools['ffprobe']))
            else:
                require(a.tools is None,'H5_MOTION_UNUSED_TOOLS')
                from .motion import inspect_motion
                result=inspect_motion(a.root,artifact,binding,policy)
            status=result['report']['status']
        encoded=json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n'
        if a.output is not None:
            with a.output.open('x',encoding='utf-8') as f:f.write(encoded)
        else:print(encoded,end='')
        return 2 if status=='BLOCKED' else 3
    except (ValueError,TypeError,KeyError,OSError,ContractError) as exc:
        print(json.dumps({'status':'BLOCKED','error':str(exc),'product_accepted':False}),file=sys.stderr);return 4
if __name__=='__main__':raise SystemExit(main())
