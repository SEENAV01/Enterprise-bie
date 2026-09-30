"""METRIC-013: decoded RGB evidence, pixel errors, blackness and required motion.
Not a perceptual aesthetic score, OCR legibility test or general video QA.
"""
import base64,binascii,hashlib
from fractions import Fraction
from ..models import BenchmarkError,digest_string
from ..domains.structured import record,sequence,amount,probability
from .common import indexed,weight
from .delivery_common import integer,result_unit,observation,used_artifacts

def pixels(row):
    w=integer(row['width'],1,320);h=integer(row['height'],1,180)
    value=row['rgb_base64']
    if type(value) is not str or len(value)>240000:raise BenchmarkError('PIXEL_PAYLOAD_LIMIT')
    try:data=base64.b64decode(value,validate=True)
    except (ValueError,binascii.Error) as exc:raise BenchmarkError('INVALID_PIXEL_ENCODING') from exc
    if len(data)!=w*h*3 or hashlib.sha256(data).hexdigest()!=digest_string(row['raw_sha256']):
        raise BenchmarkError('PIXEL_PAYLOAD_INTEGRITY_FAILURE')
    return data

def measure(reference,candidate,artifacts):
    record(reference,{'frames','motion_pairs'});record(candidate,{'observation_id','media_sha256'})
    refs=indexed(reference['frames'],{'id','index','width','height','rgb_base64','raw_sha256','max_mae','max_black_fraction','min_channel_spread','weight'},lower=1,upper=8)
    o=observation(artifacts,candidate['observation_id'],'frames',candidate['media_sha256']);used_artifacts(artifacts,[candidate['observation_id']])
    record(o['facts'],{'frames','total_frame_count'});n=integer(o['facts']['total_frame_count'],1,300)
    actual=indexed(o['facts']['frames'],{'id','index','width','height','rgb_base64','raw_sha256'},upper=8)
    if set(actual)-set(refs):raise BenchmarkError('UNREQUESTED_FRAME_OBSERVATION')
    seen=set();data={}; units=[];stats={}
    for k,a in actual.items():
        index=integer(a['index'],0,n-1)
        if index in seen:raise BenchmarkError('DUPLICATE_DECODED_FRAME_INDEX')
        seen.add(index);data[k]=pixels(a)
    rseen=set()
    for k,r in sorted(refs.items()):
        index=integer(r['index'],0,299)
        if index in rseen:raise BenchmarkError('DUPLICATE_REFERENCE_FRAME_INDEX')
        rseen.add(index);expected=pixels(r);limit=amount(r['max_mae'],maximum=255)
        black_limit=probability(r['max_black_fraction']);spread_min=integer(r['min_channel_spread'],0,255);why=[]
        if k not in actual:why.append('REQUIRED_DECODED_FRAME_MISSING')
        else:
            a=actual[k];b=data[k]
            if (a['index'],a['width'],a['height'])!=(r['index'],r['width'],r['height']):why.append('FRAME_IDENTITY_OR_DIMENSIONS_MISMATCH')
            else:
                mae=Fraction(sum(abs(x-y) for x,y in zip(b,expected)),len(b))
                black=Fraction(sum(max(b[i:i+3])<=8 for i in range(0,len(b),3)),len(b)//3)
                spread=max(b)-min(b);stats[k]={'mae_exact':str(mae),'black_fraction_exact':str(black),'channel_spread':spread}
                if mae>limit:why.append('FRAME_PIXEL_ERROR_EXCEEDED')
                if black>black_limit:why.append('UNEXPECTED_BLACK_FRAME')
                if spread<spread_min:why.append('LOW_FRAME_CHANNEL_SPREAD')
        units.append(result_unit(k,why,weight(r)))
    pairs=set()
    for i,p in enumerate(sequence(reference['motion_pairs'],lower=0,upper=16)):
        record(p,{'first','second'});a=p['first'];b=p['second']
        if type(a) is not str or type(b) is not str or a not in refs or b not in refs or a==b:raise BenchmarkError('INVALID_MOTION_PAIR')
        if (a,b) in pairs:raise BenchmarkError('DUPLICATE_MOTION_PAIR')
        pairs.add((a,b));why=[]
        if a not in data or b not in data:why.append('MOTION_EVIDENCE_MISSING')
        elif data[a]==data[b]:why.append('REQUIRED_MOTION_FROZEN')
        units.append(result_unit('motion:'+str(i),why))
    return units,[],{'assessment_scope':'TRUSTED_DECODED_RGB_SAMPLES','statistics':stats,'perceptual_quality_certified':False}
