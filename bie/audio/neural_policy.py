"""AUDIO H1-001: explicit deployment policy, never an automatic voice downgrade.

The provider's model ID is an alias, not a hash of remote neural weights. Metadata
pins and the operator deployment revision are change controls, not proof that a
provider cannot update its backend. Voice/usage references are declarations.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import re, math
from .common import AudioError, fingerprint, digest, integer, refs, locale, text, exact_fields
from .tts_contract import AudioFormat, Voice, LocaleBinding, VoiceCatalog, SynthesisSettings

PROVIDER = 'elevenlabs-neural-v1'
FIXTURE_PROVIDER = 'elevenlabs-contract-fixture-v1'
API_ORIGIN = 'https://api.elevenlabs.io'
MODEL = 'eleven_flash_v2_5'
ADAPTER_VERSION = 'bie.audio.elevenlabs/1.0.0'


def identifier(value, name):
    if type(value) is not str or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', value):
        raise AudioError('PROVIDER_IDENTIFIER_INVALID', name)
    return value


def unit(value, name, lo=0.0, hi=1.0):
    if type(value) not in (int, float) or not math.isfinite(value) or not lo <= value <= hi:
        raise AudioError('NEURAL_SETTING_INVALID', name)


@dataclass(frozen=True)
class NeuralSettings:
    stability: float = 0.5
    similarity_boost: float = 0.75
    style: float = 0.0
    use_speaker_boost: bool = True
    speed: float = 1.0
    seed: int | None = None
    def __post_init__(self):
        for k in ('stability', 'similarity_boost', 'style'): unit(getattr(self, k), k)
        unit(self.speed, 'speed', 0.7, 1.2)
        if type(self.use_speaker_boost) is not bool: raise AudioError('NEURAL_SETTING_INVALID', 'speaker boost')
        if self.seed is not None: integer(self.seed, 'seed', 0, 4294967295)
    def wire(self):
        d = asdict(self); d.pop('seed'); return d


@dataclass(frozen=True)
class NeuralDeployment:
    voice_id: str
    deployment_revision: str
    primary_language: str
    model_metadata_fingerprint: str
    voice_metadata_fingerprint: str
    rights_refs: tuple[str, ...]
    settings: NeuralSettings = NeuralSettings()
    model_id: str = 'eleven_multilingual_v2'
    language_mode: str = 'provider_auto'
    sample_rate: int = 24000
    max_chars: int = 4000
    max_response_bytes: int = 7_500_000
    deadline_seconds: float = 60.0
    socket_timeout_seconds: float = 10.0
    enable_provider_logging: bool = True
    provider_data_transfer_approved: bool = False
    schema_version: str = 'bie.audio.neural-deployment/1'
    def __post_init__(self):
        identifier(self.voice_id, 'voice id'); text(self.deployment_revision, 'deployment revision', 256)
        if self.model_id not in (MODEL, 'eleven_multilingual_v2'): raise AudioError('NEURAL_MODEL_NOT_ADOPTED')
        expected_mode = 'enforced' if self.model_id == MODEL else 'provider_auto'
        if self.language_mode != expected_mode:
            raise AudioError('NEURAL_LANGUAGE_CAPABILITY_MISMATCH', 'Multilingual v2 does not support language_code forcing')
        locale(self.primary_language)
        if not re.fullmatch('[a-z]{2}', self.primary_language):
            raise AudioError('NEURAL_EXACT_LOCALE_UNSUPPORTED', 'Use an approved ISO639-1 language; dialect forcing is not asserted')
        digest(self.model_metadata_fingerprint); digest(self.voice_metadata_fingerprint)
        refs(self.rights_refs, 'voice and usage provenance')
        if type(self.settings) is not NeuralSettings: raise AudioError('NEURAL_SETTINGS_REQUIRED')
        NeuralSettings(**asdict(self.settings))
        if type(self.sample_rate) is not int or self.sample_rate not in (16000, 22050, 24000):
            raise AudioError('NEURAL_FORMAT_NOT_ADOPTED')
        integer(self.max_chars, 'request chars', 1, 4000)
        integer(self.max_response_bytes, 'response bytes', 1024, 7_500_000)
        unit(self.deadline_seconds, 'deadline', 0.1, 180)
        unit(self.socket_timeout_seconds, 'socket timeout', 0.05, self.deadline_seconds)
        if type(self.enable_provider_logging) is not bool or type(self.provider_data_transfer_approved) is not bool:
            raise AudioError('NEURAL_POLICY_BOOLEAN')
        if self.schema_version != 'bie.audio.neural-deployment/1': raise AudioError('NEURAL_DEPLOYMENT_SCHEMA')
    def fingerprint(self): return fingerprint(self)
    @classmethod
    def from_dict(cls, value):
        exact_fields(value, tuple(cls.__dataclass_fields__))
        d = dict(value)
        if type(d['rights_refs']) is not list: raise AudioError('NEURAL_RIGHTS_ARRAY')
        exact_fields(d['settings'], tuple(NeuralSettings.__dataclass_fields__))
        d['settings'] = NeuralSettings(**d['settings']); d['rights_refs'] = tuple(d['rights_refs'])
        return cls(**d)


def neural_catalog(config, *, fixture=False, context_fingerprint=None):
    NeuralDeployment(**asdict_config(config))
    provider = FIXTURE_PROVIDER if fixture else PROVIDER
    identity = fingerprint({'adapter': ADAPTER_VERSION, 'origin': API_ORIGIN,
                            'deployment': asdict(config), 'fixture': fixture,
                            'context': context_fingerprint})
    voice = Voice(config.voice_id, provider, config.model_id+'@'+config.deployment_revision, identity,
                  config.primary_language, (LocaleBinding(config.primary_language, config.voice_id),),
                  (AudioFormat(config.sample_rate, 1),), ('character-timestamps',),
                  'provider-fixture' if fixture else 'neural-service-unverified', config.rights_refs,
                  max_chars=config.max_chars, max_utf8_bytes=config.max_chars*4,
                  same_voice_code_switching=False)
    return VoiceCatalog(identity, (voice,))


def asdict_config(config):
    if type(config) is not NeuralDeployment: raise AudioError('NEURAL_DEPLOYMENT_REQUIRED')
    d = asdict(config); d['settings'] = config.settings; return d


def request_payload(request, config, *, context=None):
    """No made-up conversion from local WPM/pitch to neural controls.

    The inherited defaults are a compatibility sentinel only; actual speed/style
    are explicit deployment settings. No exact WPM or phoneme forcing is claimed.
    """
    if request.settings != SynthesisSettings(format=AudioFormat(config.sample_rate, 1)):
        raise AudioError('NEURAL_GENERIC_SETTINGS_UNSUPPORTED', 'Use explicit neural deployment settings')
    if request.segment.languages != (config.primary_language,):
        raise AudioError('NEURAL_CODE_SWITCH_NOT_ADOPTED')
    if any(s.phonemes is not None for s in request.segment.spans):
        raise AudioError('NEURAL_IPA_NOT_ADOPTED')
    value = request.segment.spoken_text
    if len(value) > config.max_chars: raise AudioError('NEURAL_REQUEST_BUDGET')
    # Source-origin markup and provider audio tags must not become instructions.
    if any(c in value for c in '<>[]'):
        raise AudioError('NEURAL_MARKUP_REQUIRES_SPOKEN_REALIZATION')
    body = {'text': value, 'model_id': config.model_id,
            'voice_settings': config.settings.wire(), 'apply_text_normalization': 'off',
            'apply_language_text_normalization': False}
    if config.language_mode == 'enforced': body['language_code'] = config.primary_language
    if config.settings.seed is not None: body['seed'] = config.settings.seed
    if context:
        for key, ctx in context.items():
            if key not in ('previous_text','next_text') or type(ctx) is not str or len(ctx)>config.max_chars:
                raise AudioError('NEURAL_CONTEXT_BUDGET')
            if any(c in ctx for c in '<>[]'): raise AudioError('NEURAL_CONTEXT_MARKUP')
            body[key] = ctx
    return body
