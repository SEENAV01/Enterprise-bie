"""H2-004: uncertainty-aware diagnostics derived from authenticated measurements."""
from __future__ import annotations
from dataclasses import asdict
import re
from .common import AudioError, fingerprint
from .qa_contract import Finding
from .acoustic_contract import BOUNDARIES, plain, edit_distance, validate_job
from .acoustic_evidence import verify_receipt


def assess_receipt(receipt,job,trust,*,now=None):
    measurement=verify_receipt(receipt,job,trust,now=now)
    policy=validate_job(job);findings=[];comparisons=[]
    def add(code,severity,owner,segment,detail):
        refs=tuple(sorted({ref for span in segment['source_spans'] for ref in span['source_refs']}))
        findings.append(Finding(code,severity,owner,segment['segment_id'],detail,refs))
    for segment,row in zip(job['segments'],measurement['segments']):
        status=row['status']
        if status=='NO_SIGNAL':
            add('ACOUSTIC_DELIVERED_SEGMENT_SILENT','FAIL','AUDIO/MIX' if segment['dry_source_has_signal'] else 'AUDIO/VO',segment,
                'Delivered PCM is exactly zero. Route to MIX when verified dry source contains signal, otherwise VO; preserve the reading and rebuild dependents.')
            continue
        if status!='MEASURED':
            add('ACOUSTIC_'+status,'BLOCKED','AUDIO/QA',segment,
                'Independent acoustic evidence is incomplete or unsupported for this segment. No successful check is inferred.')
            continue
        if 'FIXTURE' in segment['timing_basis'] or 'SYNTHETIC' in segment['timing_basis']:
            add('ACOUSTIC_DIAGNOSTIC_SOURCE_ONLY','REVIEW','AUDIO/QA',segment,
                'A synthetic source remains a diagnostic fixture even when an independent native recognizer executes on its bytes.')
        # Compare only equal codepoint coverage. Never interpolate unmatched tokens.
        for word,phone in zip(row['words'],row['phone_comparisons']):
            providers=[p for p in segment['provider_words']
                if p['spoken_start']==word['spoken_start'] and p['spoken_end']==word['spoken_end']]
            if len(providers)!=1:
                add('ACOUSTIC_TOKEN_CLOCK_MAPPING_UNRESOLVED','REVIEW','AUDIO/SYNC',segment,
                    'Provider and independent tokenizer boundaries differ; no synthetic word-boundary correspondence was manufactured.')
            else:
                p=providers[0];start_delta=word['start_sample']-p['start_sample'];end_delta=word['end_sample']-p['end_sample']
                comparison={'segment_id':segment['segment_id'],'spoken_start':word['spoken_start'],
                    'word':word['word'],'start_delta_samples':start_delta,'end_delta_samples':end_delta,
                    'sample_rate':job['binding']['sample_rate'],'frame_resolution_ms':10}
                comparisons.append(comparison)
                if max(abs(start_delta),abs(end_delta))*1000 > policy.disagreement_ms*job['binding']['sample_rate']:
                    add('ACOUSTIC_TIMING_DISAGREEMENT','REVIEW','AUDIO/SYNC',segment,
                        'Independent constrained alignment disagrees with the provider clock beyond the diagnostic triage threshold; inspect before changing any caption or animation.')
            if phone['minimum_edit_distance']*100 > policy.max_phone_edit_percent*phone['denominator']:
                add('ACOUSTIC_PHONE_DISAGREEMENT','REVIEW','AUDIO/VO',segment,
                    'Unconstrained phone decoding differs from approved dictionary variants. This is uncalibrated evidence, not a proven pronunciation error.')
        decoded=[re.sub(r'\(\d+\)$','',x['label']) for x in row['native_passes'][2]['segments'] if not x['label'].startswith(('<','['))]
        expected=[t['word'] for t in row['tokens']]
        if decoded!=expected:
            add('ACOUSTIC_LEXICAL_DISAGREEMENT','REVIEW','AUDIO/QA',segment,
                'Independent N-gram recognition differs from the expected reading; recognizer error and genuine speech error are not distinguished without review.')
        add('ACOUSTIC_CALIBRATION_AND_LISTENING_REQUIRED','REVIEW','AUDIO/QA',segment,
            'Native frame/phone evidence is available; dialect-specific held-out calibration and independent listening are not established.')
    # Collapse duplicate diagnostics but retain word-level evidence in measurement.
    unique={fingerprint(asdict(f)):f for f in findings}
    findings=tuple(unique[k] for k in sorted(unique))
    priority={'PASS':0,'REVIEW':1,'BLOCKED':2,'FAIL':3}
    out={'schema_version':'bie.audio.acoustic-assessment/1','job_fingerprint':job['fingerprint'],
         'receipt_fingerprint':fingerprint(receipt),'trust_fingerprint':fingerprint(trust),
         'measurement_fingerprint':measurement['fingerprint'],
         'status':max(('REVIEW',*(f.severity for f in findings)),key=priority.get),
         'findings':plain([asdict(f) for f in findings]),'timing_comparisons':comparisons,
         'issuer_signature_verified':True,'authenticity_scope':'Configured local diagnostic issuer, not independent production authorization',
         'native_measured_segments':sum(r['status']=='MEASURED' for r in measurement['segments']),
         **BOUNDARIES}
    out['fingerprint']=fingerprint(out)
    return out


def _qa_index(f):
    return 3 if f['owner']=='AUDIO/SYNC' else 2 if f['owner']=='AUDIO/MIX' else 0


def adopt_into_qa(checks,binding,mixed,sync,receipt,trust,policy,*,now=None):
    """Called by the existing audit_mix; preserves all legacy acceptance boundaries."""
    from .acoustic_contract import build_job
    from .qa_contract import check
    job=build_job(mixed,sync,policy)
    assessment=assess_receipt(receipt,job,trust,now=now)
    extra=[Finding(**{**f,'source_refs':tuple(f['source_refs'])}) for f in assessment['findings']]
    updated=[]
    for index,current in enumerate(checks):
        additions=[f for f in extra if _qa_index(asdict(f))==index]
        metrics=__import__('json').loads(current.metrics_json)
        if index in (0,2,3):
            metrics['independent_acoustic_evidence']={
                'assessment':assessment,'evaluator_receipt':receipt,
                'receipt_verification_required_on_reuse':True,
                'calibrated_pronunciation_or_alignment_verified':False}
        updated.append(check(current.task_id,current.scope,(*current.findings,*additions),metrics,executed=current.executed))
    binding={**binding,'acoustic_job_fingerprint':job['fingerprint'],
             'acoustic_receipt_fingerprint':fingerprint(receipt),'evaluator_trust_fingerprint':fingerprint(trust)}
    return tuple(updated),binding


def verify_augmented_qa(report,mixed,sync,receipt,trust,policy,*,now=None):
    """Public hashes do not authenticate a reloaded augmented QA report."""
    from .qa_contract import validate_report
    from .acoustic_contract import build_job
    validate_report(report);job=build_job(mixed,sync,policy)
    assessment=assess_receipt(receipt,job,trust,now=now)
    expected={'media_sha256':job['binding']['media_sha256'],
              'mix_receipt_fingerprint':job['binding']['mix_receipt_fingerprint'],
              'clock_fingerprint':job['binding']['clock_fingerprint'],
              'source_sync_fingerprint':job['binding']['source_sync_fingerprint'],
              'acoustic_job_fingerprint':job['fingerprint'],
              'acoustic_receipt_fingerprint':fingerprint(receipt),'evaluator_trust_fingerprint':fingerprint(trust)}
    if any(report['binding'].get(k)!=v for k,v in expected.items()):raise AudioError('ACOUSTIC_QA_REPORT_BINDING')
    for index in (0,2,3):
        evidence=report['checks'][index]['metrics'].get('independent_acoustic_evidence')
        if not evidence or evidence.get('assessment')!=assessment or evidence.get('evaluator_receipt')!=receipt:
            raise AudioError('ACOUSTIC_QA_EVIDENCE_CHANGED')
        if evidence.get('receipt_verification_required_on_reuse') is not True or evidence.get('calibrated_pronunciation_or_alignment_verified') is not False:
            raise AudioError('ACOUSTIC_QA_AUTHORITY_CHANGED')
        expected_findings=[f for f in assessment['findings'] if _qa_index(f)==index]
        actual=[f for f in report['checks'][index]['findings'] if f['code'].startswith('ACOUSTIC_')]
        if actual!=expected_findings:raise AudioError('ACOUSTIC_QA_FINDINGS_CHANGED')
    return report
