"""Voice calling providers (Milestone 4).

Pluggable backends behind a common interface, selected by VOICE_PROVIDER. The
`stub` provider never places a call. A future `twilio_elevenlabs` provider will
implement real dialing + TTS once credentials are configured.
"""
from app.core.config import settings
from app.services.voice_providers.base import PlaceCallResult, VoiceProvider
from app.services.voice_providers.stub import StubVoiceProvider

_PROVIDERS = {
    "stub": StubVoiceProvider,
}


def get_voice_provider() -> VoiceProvider:
    provider_cls = _PROVIDERS.get(settings.voice_provider, StubVoiceProvider)
    return provider_cls()


__all__ = ["VoiceProvider", "PlaceCallResult", "get_voice_provider"]
