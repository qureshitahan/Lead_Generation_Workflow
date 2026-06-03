"""Voice provider interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class PlaceCallResult:
    placed: bool
    provider: str
    provider_call_id: Optional[str] = None
    error: Optional[str] = None


class VoiceProvider(ABC):
    name = "base"

    @abstractmethod
    def place_call(self, *, to_number: str, from_number: str, script: str) -> PlaceCallResult:
        ...
