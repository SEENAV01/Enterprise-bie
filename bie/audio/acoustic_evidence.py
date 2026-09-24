"""H2-003: out-of-band evaluator trust, Ed25519 receipts and strict current binding.

Signatures authenticate a configured issuer, not the truth of its model or an
untrusted host. Diagnostic test keys can never authorize product acceptance.
"""
from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
import hashlib, os, re, stat, time
from .common import AudioError, digest, fingerprint, integer, strict_json, text
from .acoustic_contract import (BOUNDARIES, RESULT_SCHEMA, SCOPE, canonical, fields,
    sha, validate_job, english_tokens, edit_distance)

MEASURE_FIELDS=('schema_version','scope','job_fingerprint','runtime_fingerprint','segments',
    'frame_resolution_ms','method','score_interpretation',*BOUNDARIES,'fingerprint')
SEGMENT_FIELDS=('segment_id','request_fingerprint','status','native_passes','tokens','words',
    'phone_comparisons','signals','crop_sha256','analysis_pcm_sha256','analysis_samples')
STATUSES=('MEASURED','UNSUPPORTED_LANGUAGE','UNSUPPORTED_TOKENIZATION','TOKEN_BUDGET',
    'UNSUPPORTED_PHONETIC_OVERRIDE','OUT_OF_VOCABULARY','NO_SIGNAL',
    'ANALYSIS_CHANNEL_CANCELLATION','ALIGNMENT_INCOMPLETE')


def validate_measurement(result,job,runtime_fingerprint=None):
    policy=validate_job(job);fields(result,MEASURE_FIELDS,'ACOUSTIC_MEASUREMENT_FIELDS')
    if result['schema_version']!=RESULT_SCHEMA or result['scope']!=SCOPE or result['job_fingerprint']!=job['fingerprint']:
        raise AudioError('ACOUSTIC_MEASUREMENT_BINDING')
    digest(result['runtime_fingerprint'])
    if runtime_fingerprint is not None and result['runtime_fingerprint']!=runtime_fingerprint:
        raise AudioError('ACOUSTIC_MEASUREMENT_RUNTIME')
    if any(type(result[k]) is not type(v) or result[k]!=v for k,v in BOUNDARIES.items()):
        raise AudioError('ACOUSTIC_UNCALIBRATED_ACCEPTANCE')
    if type(result['frame_resolution_ms']) is not int or result['frame_resolution_ms']!=10 or result['method']!='TRANSCRIPT_CONSTRAINED_WORD_FSG_PLUS_UNCONSTRAINED_ALLPHONE_AND_NGRAM':
        raise AudioError('ACOUSTIC_MEASUREMENT_METHOD')
    text(result['score_interpretation'],'score interpretation',1000)
    if type(result['segments']) is not list or len(result['segments'])!=len(job['segments']):
        raise AudioError('ACOUSTIC_MEASUREMENT_COVERAGE')
    for row,seg in zip(result['segments'],job['segments']):
        fields(row,SEGMENT_FIELDS,'ACOUSTIC_MEASUREMENT_SEGMENT')
        if row['segment_id']!=seg['segment_id'] or row['request_fingerprint']!=seg['request_fingerprint'] or row['status'] not in STATUSES:
            raise AudioError('ACOUSTIC_MEASUREMENT_SEGMENT_BINDING')
        sha(row['crop_sha256'])
        if row['analysis_pcm_sha256'] is not None:sha(row['analysis_pcm_sha256'])
        integer(row['analysis_samples'],'analysis samples',0,960002)
        for key in ('native_passes','tokens','words','phone_comparisons','signals'):
            if type(row[key]) is not list:raise AudioError('ACOUSTIC_MEASUREMENT_COLLECTION')
        if row['signals']:raise AudioError('ACOUSTIC_UNKNOWN_SIGNAL')
        if row['status']=='UNSUPPORTED_LANGUAGE':
            if seg['languages'] in (['en'],['en-US']) or row['native_passes'] or row['tokens'] or row['words'] or row['analysis_samples']:
                raise AudioError('ACOUSTIC_UNSUPPORTED_LANGUAGE_TAMPER')
        if row['status'] in ('MEASURED','ALIGNMENT_INCOMPLETE'):
            if seg['languages'] not in (['en'],['en-US']):raise AudioError('ACOUSTIC_FALSE_LANGUAGE_CAPABILITY')
            if any(sp.get('phonemes') is not None for sp in seg['source_spans']):raise AudioError('ACOUSTIC_FALSE_IPA_CAPABILITY')
            if row['tokens']!=english_tokens(seg['spoken_text']) or not row['analysis_samples'] or row['analysis_pcm_sha256'] is None:
                raise AudioError('ACOUSTIC_TOKEN_COVERAGE')
            if len(row['native_passes'])!=3:raise AudioError('ACOUSTIC_NATIVE_PASSES_REQUIRED')
        elif row['native_passes'] or row['words'] or row['phone_comparisons']:
            raise AudioError('ACOUSTIC_UNEXECUTED_EVIDENCE')
        for token in row['tokens']:
            fields(token,('word','spoken_start','spoken_end'))
            text(token['word'],'evaluation token',256)
            integer(token['spoken_start'],'token start',0,len(seg['spoken_text'])-1)
            integer(token['spoken_end'],'token end',token['spoken_start']+1,len(seg['spoken_text']))
        maxframe=(row['analysis_samples']+159)//160+3
        for data,mode in zip(row['native_passes'],('fsg','allphone','lm')):
            fields(data,('hypothesis','score_raw','segments','mode','confidence'))
            if data['mode']!=mode or data['confidence'] is not None or type(data['hypothesis']) is not str or len(data['hypothesis'])>65536:
                raise AudioError('ACOUSTIC_NATIVE_PASS_IDENTITY')
            integer(data['score_raw'],'raw score',-2**63,2**63-1)
            if type(data['segments']) is not list or len(data['segments'])>8192:raise AudioError('ACOUSTIC_NATIVE_SEGMENT_BUDGET')
            last=0
            for sample in data['segments']:
                fields(sample,('label','start_frame','end_frame_exclusive','acoustic_score_raw','language_score_raw'))
                text(sample['label'],'native label',256)
                integer(sample['start_frame'],'frame start',0,maxframe)
                integer(sample['end_frame_exclusive'],'frame end',sample['start_frame']+1,maxframe)
                for key in ('acoustic_score_raw','language_score_raw'):integer(sample[key],key,-2**63,2**63-1)
                if sample['start_frame']<last:raise AudioError('ACOUSTIC_NATIVE_FRAME_ORDER')
                last=sample['end_frame_exclusive']
        if row['status']=='MEASURED':
            if len(row['tokens'])!=len(row['words']) or len(row['phone_comparisons'])!=len(row['tokens']):
                raise AudioError('ACOUSTIC_WORD_PHONE_COVERAGE')
            forced=[w for w in row['native_passes'][0]['segments'] if not w['label'].startswith(('<','['))]
            if len(forced)!=len(row['tokens']):raise AudioError('ACOUSTIC_FORCED_WORD_COVERAGE')
            phone_rows=[p for p in row['native_passes'][1]['segments'] if p['label'] not in ('SIL','<sil>','<s>','</s>')]
            end=seg['start_sample']
            for word,token,phone,raw in zip(row['words'],row['tokens'],row['phone_comparisons'],forced):
                fields(word,('word','spoken_start','spoken_end','start_sample','end_sample','acoustic_score_raw'))
                for key in ('spoken_start','spoken_end','start_sample','end_sample'):
                    integer(word[key],key,0,100_000_000)
                integer(word['acoustic_score_raw'],'word score',-2**63,2**63-1)
                if any(word[k]!=token[k] for k in token) or re.sub(r'\(\d+\)$','',raw['label'])!=token['word']:
                    raise AudioError('ACOUSTIC_FORCED_TEXT_CHANGED')
                a=seg['start_sample']+(raw['start_frame']*job['binding']['sample_rate']+50)//100
                b=min(seg['end_sample'],seg['start_sample']+(raw['end_frame_exclusive']*job['binding']['sample_rate']+50)//100)
                if word['start_sample']!=a or word['end_sample']!=b or not end<=a<b<=seg['end_sample'] or word['acoustic_score_raw']!=raw['acoustic_score_raw']:
                    raise AudioError('ACOUSTIC_NATIVE_MAPPING_CHANGED')
                end=b
                fields(phone,('word','spoken_start','expected_variants','observed_phones','minimum_edit_distance','selected_variant_index','denominator','confidence'))
                if phone['word']!=token['word'] or phone['spoken_start']!=token['spoken_start'] or phone['confidence'] is not None:
                    raise AudioError('ACOUSTIC_PHONE_BINDING')
                for key in ('minimum_edit_distance','selected_variant_index','denominator','spoken_start'):
                    integer(phone[key],key,0,1_000_000)
                variants=phone['expected_variants']
                if type(variants) is not list or not 1<=len(variants)<=32:raise AudioError('ACOUSTIC_PHONE_VARIANTS')
                for variant in variants:
                    if type(variant) is not list or not 1<=len(variant)<=256:raise AudioError('ACOUSTIC_PHONE_VARIANT')
                    for p in variant:text(p,'phone',64)
                assigned=[p['label'] for p in phone_rows if 2*raw['start_frame']<=p['start_frame']+p['end_frame_exclusive']<2*raw['end_frame_exclusive']]
                if phone['observed_phones']!=assigned:raise AudioError('ACOUSTIC_PHONE_ASSIGNMENT')
                distance,index=min((edit_distance(v,assigned),i) for i,v in enumerate(variants))
                if phone['minimum_edit_distance']!=distance or phone['selected_variant_index']!=index or phone['denominator']!=max(1,len(variants[index])):
                    raise AudioError('ACOUSTIC_PHONE_METRIC_TAMPER')
    if fingerprint({k:v for k,v in result.items() if k!='fingerprint'})!=result['fingerprint']:
        raise AudioError('ACOUSTIC_MEASUREMENT_TAMPER')
    return result


def load_private_key(path):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    p=Path(path).absolute()
    if any(x.is_symlink() for x in (p,*p.parents)):raise AudioError('ACOUSTIC_PRIVATE_KEY_SYMLINK')
    fd=os.open(p,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0))
    try:
        st=os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_uid!=os.getuid() or st.st_mode&0o077 or st.st_size!=32:
            raise AudioError('ACOUSTIC_PRIVATE_KEY_PERMISSIONS')
        raw=os.read(fd,33)
        if len(raw)!=32:raise AudioError('ACOUSTIC_PRIVATE_KEY_FORMAT')
        return Ed25519PrivateKey.from_private_bytes(raw)
    finally:os.close(fd)


def validate_trust(trust):
    fields(trust,('schema_version','revision','issuers','max_age_seconds','max_future_skew_seconds','scope'))
    if trust['schema_version']!='bie.audio.evaluator-trust/1' or trust['scope']!=SCOPE:
        raise AudioError('ACOUSTIC_TRUST_SCHEMA')
    text(trust['revision'],'trust revision',256)
    integer(trust['max_age_seconds'],'max age',1,86400)
    integer(trust['max_future_skew_seconds'],'future skew',0,300)
    if type(trust['issuers']) is not list or not 1<=len(trust['issuers'])<=100:
        raise AudioError('ACOUSTIC_TRUST_ISSUERS')
    seen=set()
    for issuer in trust['issuers']:
        fields(issuer,('key_id','public_key_hex','role','runtime_fingerprints','not_before','not_after','revoked'))
        text(issuer['key_id'],'key id',256)
        if issuer['key_id'] in seen:raise AudioError('ACOUSTIC_DUPLICATE_ISSUER')
        seen.add(issuer['key_id']);sha(issuer['public_key_hex'])
        if issuer['public_key_hex']=='0'*64 or issuer['role']!='acoustic-evaluator' or type(issuer['revoked']) is not bool:
            raise AudioError('ACOUSTIC_ISSUER_ROLE')
        integer(issuer['not_before'],'not before',0,2**53)
        integer(issuer['not_after'],'not after',issuer['not_before']+1,2**53)
        if type(issuer['runtime_fingerprints']) is not list or not issuer['runtime_fingerprints']:
            raise AudioError('ACOUSTIC_ISSUER_RUNTIME_ALLOWLIST')
        for runtime in issuer['runtime_fingerprints']:digest(runtime)
    return trust


def issue_evaluation(job,wav,runtime,private_key,key_id,*,cancellation=None,now=None):
    """Measure internally, then sign. Does not sign caller-provided result JSON."""
    from .acoustic_runtime import run_native
    text(key_id,'key id',256)
    result=run_native(job,wav,runtime,cancellation=cancellation)
    issued=int(time.time()) if now is None else now
    integer(issued,'issue time',0,2**53)
    payload={'schema_version':'bie.audio.evaluator-payload/1','key_id':key_id,
             'scope':SCOPE,'issued_at':issued,'expires_at':issued+600,
             'job_fingerprint':job['fingerprint'],'binding':job['binding'],
             'measurement':result,**BOUNDARIES}
    signature=private_key.sign(b'BIE-AUDIO-EVALUATOR-V1\0'+canonical(payload)).hex()
    return {'schema_version':'bie.audio.signed-evaluation/1','payload':payload,
            'signature_ed25519_hex':signature}


def verify_receipt(receipt,current_job,trust,*,now=None):
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    validate_job(current_job);validate_trust(trust)
    fields(receipt,('schema_version','payload','signature_ed25519_hex'),'ACOUSTIC_RECEIPT_FIELDS')
    if receipt['schema_version']!='bie.audio.signed-evaluation/1':raise AudioError('ACOUSTIC_RECEIPT_SCHEMA')
    payload=receipt['payload']
    fields(payload,('schema_version','key_id','scope','issued_at','expires_at','job_fingerprint','binding','measurement',*BOUNDARIES))
    if payload['schema_version']!='bie.audio.evaluator-payload/1' or payload['scope']!=SCOPE or any(type(payload[k]) is not type(v) or payload[k]!=v for k,v in BOUNDARIES.items()):
        raise AudioError('ACOUSTIC_RECEIPT_AUTHORITY')
    issuer=next((i for i in trust['issuers'] if i['key_id']==payload['key_id']),None)
    if issuer is None:raise AudioError('ACOUSTIC_UNKNOWN_ISSUER')
    if issuer['revoked']:raise AudioError('ACOUSTIC_ISSUER_REVOKED')
    signature=receipt['signature_ed25519_hex']
    if type(signature) is not str or re.fullmatch('[0-9a-f]{128}',signature) is None:
        raise AudioError('ACOUSTIC_SIGNATURE_FORMAT')
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(issuer['public_key_hex'])).verify(
            bytes.fromhex(signature),b'BIE-AUDIO-EVALUATOR-V1\0'+canonical(payload))
    except (InvalidSignature,ValueError) as exc:raise AudioError('ACOUSTIC_SIGNATURE_INVALID') from exc
    current=int(time.time()) if now is None else now;integer(current,'verification time',0,2**53)
    integer(payload['issued_at'],'issued at',0,2**53);integer(payload['expires_at'],'expires at',payload['issued_at']+1,2**53)
    if (payload['issued_at']>current+trust['max_future_skew_seconds'] or current>=payload['expires_at']
        or current-payload['issued_at']>trust['max_age_seconds']
        or payload['expires_at']-payload['issued_at']>trust['max_age_seconds']
        or not issuer['not_before']<=payload['issued_at']<issuer['not_after']
        or not issuer['not_before']<=current<issuer['not_after']):
        raise AudioError('ACOUSTIC_RECEIPT_EXPIRED_OR_FUTURE')
    if payload['job_fingerprint']!=current_job['fingerprint'] or payload['binding']!=current_job['binding']:
        raise AudioError('ACOUSTIC_RECEIPT_STALE_BINDING')
    result=payload['measurement'];validate_measurement(result,current_job)
    if result['runtime_fingerprint'] not in issuer['runtime_fingerprints']:
        raise AudioError('ACOUSTIC_UNTRUSTED_RUNTIME')
    return result
