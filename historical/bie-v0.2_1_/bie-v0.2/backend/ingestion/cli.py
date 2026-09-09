import argparse
from .ingest import ingest_pdf, save_json

p=argparse.ArgumentParser()
p.add_argument('input_pdf'); p.add_argument('output_json')
a=p.parse_args()
save_json(ingest_pdf(a.input_pdf), a.output_json)
print(f"Wrote {a.output_json}")
