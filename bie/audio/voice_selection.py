"""BIE-AUDIO-VO-008: deterministic capability/continuity selection, no voice guesses."""
from dataclasses import dataclass
from .common import AudioError,digest,fingerprint,refs,text
from .speech_contract import SpeechPlan
from .tts_contract import Voice,VoiceCatalog,SynthesisSettings,SynthesisRequest


@dataclass(frozen=True)
class SelectionPolicy:
    allowed_providers: tuple[str,...]
    allowed_quality_classes: tuple[str,...]
    preferred_voices: tuple[str,...] = ()
    require_same_voice_code_switching: bool = True
    def __post_init__(self):
        refs(self.allowed_providers,'provider allowlist');refs(self.allowed_quality_classes,'quality allowlist')
        refs(self.preferred_voices,'voice preferences',False)
        if type(self.require_same_voice_code_switching)is not bool:raise AudioError('VOICE_POLICY_BOOLEAN')


@dataclass(frozen=True)
class PersonaSelection:
    persona_id: str
    voice: Voice
    candidate_count: int


@dataclass(frozen=True)
class Selection:
    plan_fingerprint: str
    catalog_fingerprint: str
    policy: SelectionPolicy
    settings: SynthesisSettings
    personas: tuple[PersonaSelection,...]
    def fingerprint(self):return fingerprint(self)


def select_voices(plan: SpeechPlan, catalog: VoiceCatalog, policy: SelectionPolicy,
                  settings=SynthesisSettings(), *, prior: Selection | None = None) -> Selection:
    if type(plan)is not SpeechPlan or type(catalog)is not VoiceCatalog or type(policy)is not SelectionPolicy or type(settings)is not SynthesisSettings:
        raise AudioError('VOICE_SELECTION_INPUT')
    plan.require_ready()
    if prior is not None and type(prior)is not Selection:raise AudioError('PRIOR_SELECTION_REQUIRED')
    grouped={}
    for s in plan.segments:grouped.setdefault(s.persona_id,[]).append(s)
    old={x.persona_id:x.voice for x in prior.personas} if prior else {}
    out=[]
    for persona,segments in sorted(grouped.items()):
        languages={l for s in segments for l in s.languages}
        base=segments[0].language;eligible=[]
        for voice in catalog.voices:
            if voice.provider_id not in policy.allowed_providers or voice.quality_class not in policy.allowed_quality_classes:continue
            if voice.primary_language!=base:continue
            if len(languages)>1 and policy.require_same_voice_code_switching and not voice.same_voice_code_switching:continue
            try:
                for s in segments:SynthesisRequest(plan.fingerprint(),s,voice,catalog.fingerprint(),fingerprint(policy),settings)
            except AudioError:continue
            eligible.append(voice)
        if not eligible:raise AudioError('NO_COMPATIBLE_VOICE',persona)
        def rank(v):
            preference=policy.preferred_voices.index(v.voice_id) if v.voice_id in policy.preferred_voices else len(policy.preferred_voices)
            return (preference,policy.allowed_providers.index(v.provider_id),v.voice_id)
        eligible.sort(key=rank)
        if persona in old:
            # No silent model/voice upgrade or language-driven character change.
            exact=[v for v in eligible if v==old[persona]]
            if not exact:raise AudioError('VOICE_CONTINUITY_REAPPROVAL_REQUIRED',persona)
            selected=exact[0]
        else:selected=eligible[0]
        out.append(PersonaSelection(persona,selected,len(eligible)))
    return Selection(plan.fingerprint(),catalog.fingerprint(),policy,settings,tuple(out))


def requests_for(plan, catalog, selection):
    if type(selection)is not Selection:raise AudioError('SELECTION_REQUIRED')
    if plan.fingerprint()!=selection.plan_fingerprint or catalog.fingerprint()!=selection.catalog_fingerprint:raise AudioError('STALE_VOICE_SELECTION')
    check=select_voices(plan,catalog,selection.policy,selection.settings,prior=selection)
    if check!=selection:raise AudioError('EDITED_VOICE_SELECTION')
    by={x.persona_id:x.voice for x in selection.personas}
    return tuple(SynthesisRequest(plan.fingerprint(),s,by[s.persona_id],catalog.fingerprint(),selection.fingerprint(),selection.settings) for s in plan.segments)
