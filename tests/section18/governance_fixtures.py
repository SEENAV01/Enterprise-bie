"""Actual configuration persistence; diagnostic inputs, never live acceptance."""
from quality_fixtures import release_inputs
def prepare(service,p,run):
    g=service.governance
    policy=dict(model_policy='offline_only',locale='en',deterministic=True,limits={'pdf_bytes':service.limit})
    a=g.save(p,'policy','native-policy',policy,0,'native-save')
    g.activate(p,'policy','native-policy',1,a['configuration_sha256'],None,'native-active')
    with service.catalog.tx(read_only=True) as db:_,body=service.catalog.intent(db,p,run)
    m,policy,assessments=release_inputs(body)
    g.save(p,'benchmark','native-benchmark',dict(manifest=m,policy=policy),0,'native-benchmark')
