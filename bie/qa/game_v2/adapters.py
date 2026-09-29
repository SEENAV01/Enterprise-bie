"""Loss-aware adapter for inspected Section15 BrowserEvidence snapshot.

Read from a68e054025b8fe7756a71e998d9e9103dad8e0f4. Does not import/run or alter
Section15. In particular an about:blank injected smoke bundle is not an entrypoint
run and studio_grade is not a scientific learning-quality measurement.
"""
from ..release_v2.contracts import ContractError,ArtifactRef,sha256,integer
from .models import string
FIELDS={'target','execution_mode','browser_version','studio_grade','slide_deck','entity_count','external_requests','console_errors','page_errors','runtime_binding_keys','bundle_sha256','product_accepted','sandbox_uid','sandbox_no_new_privs','renderer_seccomp','canonical_worker_blob'}
def inspect_native_browser(raw,bundle):
    if type(raw) is not dict or set(raw)!=FIELDS or type(bundle) is not ArtifactRef:raise ContractError('GAME_NATIVE_BROWSER_FIELDS')
    if raw['product_accepted'] is not False:raise ContractError('GAME_NATIVE_ACCEPTANCE_CLAIM')
    for k in ('studio_grade','slide_deck','sandbox_no_new_privs','renderer_seccomp'):
        if type(raw[k]) is not bool:raise ContractError('GAME_NATIVE_BOOLEAN')
    for k in ('target','execution_mode','browser_version','canonical_worker_blob'):string(raw[k],k,2048)
    for k in ('entity_count','sandbox_uid'):integer(raw[k],k)
    for k in ('external_requests','console_errors','page_errors','runtime_binding_keys'):
        if type(raw[k]) not in (list,tuple) or len(raw[k])>4096 or any(type(x) is not str for x in raw[k]):raise ContractError('GAME_NATIVE_ARRAY')
    sha256(raw['bundle_sha256'],'bundle')
    if raw['bundle_sha256']!=bundle.sha256:raise ContractError('GAME_NATIVE_BUNDLE_MISMATCH')
    return dict(target=raw['target'],execution_mode=raw['execution_mode'],reported_entity_count=raw['entity_count'],reported_errors=bool(raw['external_requests'] or raw['console_errors'] or raw['page_errors']),requires_entrypoint_capture=True,requires_independent_ui_oracle=True,artifact_bytes_verified=False,execution_authenticated=False,native_game_acceptance=False,product_accepted=False)
