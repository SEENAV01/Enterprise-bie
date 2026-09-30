"""Content-addressed structured candidate bundle. Not a native media attestation.

For the hardened production gate, manifest.artifact_sha256 hashes this canonical
bundle. Every selected candidate is present, and matches its case context pin.
Reference answers/rubrics are held separately. Large/native files remain governed
by separately signed native evidence; no hash here asserts unseen video quality.
"""
from ..models import BenchmarkError, canonical_json, digest, exact_fields, ident
from .contracts import context


def verify_bundle(manifest, bundle):
    exact_fields(bundle, {'schema_version', 'candidates'})
    if bundle['schema_version'] != '1.0.0' or type(bundle['candidates']) is not dict:
        raise BenchmarkError('INVALID_CANDIDATE_BUNDLE')
    canonical_json(bundle)
    expected = {}
    for row in manifest['cases']:
        ctx = context(row['context'])
        if ctx['case_id'] in expected:
            raise BenchmarkError('DUPLICATE_MANIFEST_CASE')
        expected[ctx['case_id']] = ctx['candidate_sha256']
    if not expected or set(bundle['candidates']) != set(expected):
        raise BenchmarkError('CANDIDATE_BUNDLE_ROSTER_MISMATCH')
    for case, value in bundle['candidates'].items():
        ident(case)
        if digest(value) != expected[case]:
            raise BenchmarkError('CANDIDATE_BUNDLE_CONTENT_MISMATCH')
    if digest(bundle) != manifest['artifact_sha256']:
        raise BenchmarkError('CANDIDATE_BUNDLE_ARTIFACT_MISMATCH')
    return {'verified_cases': len(expected), 'bundle_sha256': digest(bundle), 'native_artifact_verified': False}
