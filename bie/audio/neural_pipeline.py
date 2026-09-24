"""H1-004: adopted neural media through the existing VO/SYNC/MIX/QA objects.

No alternate clocks or manual Scene IR. Fixture route requires explicit opt-in;
its provider identity and evidence remain visibly distinct from remote speech.
"""
from __future__ import annotations
from threading import Event
from .common import AudioError
from .neural_policy import PROVIDER, FIXTURE_PROVIDER
from .elevenlabs_provider import ElevenLabsProvider
from .tts_contract import SynthesisSettings, AudioFormat
from .voice_selection import SelectionPolicy, select_voices, requests_for
from .sync_pipeline import SynchronizedAudio
from .caption_alignment import CaptionPolicy, align_captions
from .scene_sync import assemble_scenes
from .pause_sync import synchronize_pauses
from .sync_contract import FrameRate


def prepare_neural_sync(plan, provider, cache, *, caption_policy=CaptionPolicy(), fps=FrameRate(),
                        budgets=(), prior_selection=None, cancellation=None, allow_fixture=False):
    if type(provider)is not ElevenLabsProvider:raise AudioError('NEURAL_PROVIDER_REQUIRED')
    if provider.fixture and not allow_fixture:raise AudioError('NEURAL_FIXTURE_OPT_IN_REQUIRED')
    cancel=cancellation or Event();plan.require_ready()
    catalog=provider.catalog()
    policy=SelectionPolicy((provider.provider_id,),('provider-fixture' if provider.fixture else 'neural-service-unverified',))
    settings=SynthesisSettings(format=AudioFormat(provider.config.sample_rate,1))
    selection=select_voices(plan,catalog,policy,settings,prior=prior_selection)
    requests=requests_for(plan,catalog,selection)
    provider.preflight(requests)
    assets=[];alignments=[];events=[];captions=[];hits=[]
    for r in requests:
        if cancel.is_set():raise AudioError('CANCELLED')
        outcome=cache.get_or_generate(r,provider,cancellation=cancel)
        a,e=provider.alignment_for(outcome.asset,cancellation=cancel)
        assets.append(outcome.asset);alignments.append(a);events.append(e)
        captions.append(align_captions(outcome.asset,a,caption_policy));hits.append(outcome.cache_hit)
    assets,alignments,captions=tuple(assets),tuple(alignments),tuple(captions)
    timeline,wav=assemble_scenes(plan,assets,alignments,fps=fps,budgets=budgets)
    pauses=synchronize_pauses(timeline,wav,assets,alignments,captions)
    return SynchronizedAudio(plan,selection,assets,alignments,tuple(events),captions,timeline,wav,pauses,tuple(hits))


def provider_evidence_files(sync,provider):
    """Export exact successful response bytes and redacted receipts, never keys.

    These remain same-provider timing evidence. They are not independent acoustic
    verdicts. The private response-store seal is checked again before export.
    """
    import hashlib
    from .neural_store import canonical
    if type(provider)is not ElevenLabsProvider:raise AudioError('NEURAL_PROVIDER_REQUIRED')
    files={};evidence=[]
    for i,asset in enumerate(sync.assets):
        alignment,item=provider.alignment_for(asset)
        if alignment!=sync.alignments[i]:raise AudioError('NEURAL_PUBLICATION_ALIGNMENT_CHANGED')
        reply,decoded=provider._reply(asset.request,network=False)
        if item['response_sha256']!=hashlib.sha256(reply.body).hexdigest():raise AudioError('NEURAL_PUBLICATION_RESPONSE_CHANGED')
        name=f'neural-response-{i:05d}.json';files[name]=reply.body
        evidence.append({**item,'response_file':name,'alignment_fingerprint':alignment.fingerprint()})
    files['neural-evidence.json']=canonical({'schema_version':'bie.audio.neural-publication/1',
                'source_plan_fingerprint':sync.plan.fingerprint(),'items':evidence,
                'acoustic_alignment_verified':False,'provider_signature_verified':False,'product_accepted':False})
    return files
