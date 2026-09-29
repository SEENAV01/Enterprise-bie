"""Export prescribed PNG samples from actual decoded movie bytes. New directory only."""
from pathlib import Path
import hashlib,json
from ..source_v2.io import SnapshotStore
from .media import inspect_bytes
from .metrics import sample_indices,image
from ..release_v2.contracts import ContractError

def export_samples(video_ref,artifact_root,policy,output,*,tools=None):
    output=Path(output)
    if output.exists():raise ContractError('VIDEO_CAPTURE_DESTINATION_EXISTS')
    with SnapshotStore(artifact_root) as store:data=store.read(video_ref)
    observation=inspect_bytes(data,policy,tools);indices=sample_indices(policy)
    if any(i>=observation.frames_count for i in indices):raise ContractError('VIDEO_REQUIRED_SAMPLE_MISSING')
    output.mkdir(parents=True,exist_ok=False);rows=[]
    for i in indices:
        name=f'frame_{i:06}.png';path=output/name
        image(observation.frames[i],observation.width,observation.height).save(path,format='PNG')
        payload=path.read_bytes();rows.append(dict(frame=i,pts=observation.pts[i],time_base=str(observation.time_base),path=name,bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest(),rgb_sha256=hashlib.sha256(observation.frames[i]).hexdigest()))
    receipt=dict(schema_version='bie.qa.video.samples/1',video_sha256=video_ref.sha256,policy_digest=policy.content_digest,decoded_frames=observation.frames_count,tools_digest=observation.tools_digest,probe_sha256=observation.probe_sha256,samples=rows,product_accepted=False)
    (output/'CAPTURE.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt
