"""Email provider interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class SendResult:
    sent: bool
    provider: str
    message_id: Optional[str] = None
    error: Optional[str] = None


class EmailProvider(ABC):
    name = "base"

    @abstractmethod
    def send(self, *, to_email: str, subject: str, body: str, from_email: str, from_name: str) -> SendResult:
        ...
