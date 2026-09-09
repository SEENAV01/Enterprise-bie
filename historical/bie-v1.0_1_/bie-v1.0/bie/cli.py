
import argparse, json
from .pipeline import run_book

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--out",default="artifacts")
    args=ap.parse_args()
    result=run_book(args.pdf,args.out)
    print(json.dumps({"decision":result["m5"]["decision"],"artifacts":args.out},indent=2))
if __name__=="__main__": main()
