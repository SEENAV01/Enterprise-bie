"""Read actual artifact bytes. Identity and valid PNG bytes are not visual truth."""
from dataclasses import asdict
from io import BytesIO
import warnings
from ..release_v2.contracts import ContractError
from ..source_v2.codec import loads
from ..source_v2.io import SnapshotStore

CAPTURE_FIELDS={'schema_version','html_sha256','screenshot_sha256','viewport','state','renderer_id','renderer_version','mode','unsupported'}


def verify_capture(capture,state,view,store):
    html=store.read(capture.html);raw=store.read(capture.measurements);png=store.read(capture.screenshot)
    data=loads(raw)
    if type(data) is not dict or set(data)!=CAPTURE_FIELDS: raise ContractError('VIS_CAPTURE_FIELDS')
    # Compare JSON-shaped records, including each line rectangle and exact text.
    from ..release_v2.contracts import canonical_bytes
    if canonical_bytes(data['state'])!=canonical_bytes(asdict(state)): raise ContractError('VIS_CAPTURE_STATE_MISMATCH')
    if data['schema_version']!='1.0.0' or data['mode']!='static-html-sample': raise ContractError('VIS_CAPTURE_MODE')
    if data['html_sha256']!=capture.html.sha256 or data['screenshot_sha256']!=capture.screenshot.sha256:
        raise ContractError('VIS_CAPTURE_HASH_BINDING')
    if data['viewport']!=[view.width_px,view.height_px]: raise ContractError('VIS_CAPTURE_VIEW_MISMATCH')
    if (data['renderer_id'],data['renderer_version'])!=(capture.renderer_id,capture.renderer_version):
        raise ContractError('VIS_CAPTURE_RENDERER_MISMATCH')
    if type(data['unsupported']) is not list or len(data['unsupported'])>128 or any(type(x) is not str for x in data['unsupported']):
        raise ContractError('VIS_CAPTURE_UNSUPPORTED_FIELDS')
    if not html.strip(): raise ContractError('VIS_EMPTY_HTML')
    try:
        from PIL import Image
        with warnings.catch_warnings():
            warnings.simplefilter('error',Image.DecompressionBombWarning)
            with Image.open(BytesIO(png)) as image:
                if image.format!='PNG' or image.size!=(view.width_px,view.height_px) or getattr(image,'n_frames',1)!=1:
                    raise ContractError('VIS_CAPTURE_PNG_DIMENSIONS_OR_FORMAT')
                image.verify()
            with Image.open(BytesIO(png)) as image: image.load()
    except ImportError as exc: raise ContractError('VIS_PNG_DECODER_UNAVAILABLE') from exc
    except (OSError,ValueError,Warning) as exc:
        if isinstance(exc,ContractError): raise
        raise ContractError('VIS_CAPTURE_PNG_INVALID') from exc
    return tuple(data['unsupported'])
