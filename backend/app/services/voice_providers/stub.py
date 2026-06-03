"""Stub voice provider — never places a real call."""
from __future__ import annotations

from app.services.voice_providers.base import PlaceCallResult, VoiceProvider


class StubVoiceProvider(VoiceProvider):
    name = "stub"

    def place_call(self, *, to_number: str, from_number: str, script: str) -> PlaceCallResult:
        # Safe default: no outbound call is made in the MVP.
        return PlaceCallResult(
            placed=False,
            provider=self.name,
            error="Stub provider: calling disabled. Configure VOICE_PROVIDER to enable.",
        )
