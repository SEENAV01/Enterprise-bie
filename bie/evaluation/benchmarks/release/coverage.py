"""Pinned full domain x 17-metric coverage; no diagonal-only aggregate shortcut.

The production contract states minimum independent reference groups per cell.
Same reference content cannot inflate counts under fresh case/group IDs. This
structural check does not prove holdout secrecy or independent golden review.
No implicit not-applicable exemptions are supported by this contract version.
"""
from ..models import BenchmarkError, digest, exact_fields
from .contracts import keyed_rows, pinned, bounded_int

ALL = {f'BIE-EVAL-METRIC-{i:03}' for i in range(1,18)}


def verify_coverage(manifest, contract, *, expected_sha256):
    pinned(contract, expected_sha256)
    exact_fields(contract, {'schema_version','domains'})
    if contract['schema_version'] != '1.0.0':
        raise BenchmarkError('INVALID_COVERAGE_CONTRACT_VERSION')
    domains = keyed_rows(contract['domains'], {'id','metrics'}, lower=1)
    actual_domains = {r['context']['domain'] for r in manifest['cases']}
    if set(domains) != actual_domains:
        raise BenchmarkError('COVERAGE_DOMAIN_ROSTER_MISMATCH')
    records = []; reasons = []
    for name, domain in sorted(domains.items()):
        metrics = keyed_rows(domain['metrics'], {'id','minimum_groups'}, lower=17, upper=17)
        if set(metrics) != ALL:
            raise BenchmarkError('COVERAGE_METRIC_ROSTER_INCOMPLETE')
        for metric, policy in sorted(metrics.items()):
            minimum = bounded_int(policy['minimum_groups'],1,1000)
            rows = [r for r in manifest['cases'] if r['context']['domain']==name and r['context']['metric_id']==metric]
            # Connected components merge reused reference hashes or leakage group names.
            parents = list(range(len(rows)))
            def root(i):
                while parents[i] != i:
                    parents[i] = parents[parents[i]]; i = parents[i]
                return i
            seen_ref = {}; seen_group = {}
            for i,r in enumerate(rows):
                for seen,key in ((seen_ref,r['context']['reference_sha256']), (seen_group,r['leakage_group'])):
                    if key in seen: parents[root(i)] = root(seen[key])
                    else: seen[key] = i
            groups = len({root(i) for i in range(len(rows))})
            if groups < minimum: reasons.append('DOMAIN_METRIC_COVERAGE_INCOMPLETE')
            records.append({'domain':name,'metric_id':metric,'cases':len(rows),'independent_groups':groups,'minimum_groups':minimum})
    return {'status':'BLOCKED' if reasons else 'VERIFIED','reasons':sorted(set(reasons)), 'cells':records,
            'coverage_contract_sha256':digest(contract),'golden_quality_certified':False}
