"""Local credential-gated Section 18 candidate. Never binds publicly by default."""
import argparse, os, sys, time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from apps.operator.contracts import Credentials, Principal, PERMISSIONS, require
from apps.operator.service import Service
from apps.operator.main import create_app

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root',type=Path,required=True)
    parser.add_argument('--port',type=int,default=8080)
    args=parser.parse_args()
    token=os.environ.get('BIE_OPERATOR_TOKEN','')
    credentials=Credentials()
    credentials.grant(token,Principal('local-operator','local',PERMISSIONS,time.time()+8*3600))
    require(1024<=args.port<=65535,'invalid_port')
    import uvicorn
    uvicorn.run(create_app(Service(args.data_root,credentials)),host='127.0.0.1',port=args.port,
                access_log=False,log_level='warning')

if __name__=='__main__':
    try: main()
    except Exception:
        print('Operator startup failed; check private storage and process credential configuration.',file=sys.stderr)
        raise SystemExit(2)
