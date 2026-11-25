"""Abstract provider interfaces for WhatsApp, SMS, Email, and In-App notifications."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum


class NotificationChannel(StrEnum):
    WHATSAPP = "whatsapp"
    SMS = "sms"
    EMAIL = "email"
    IN_APP = "in_app"


@dataclass
class NotificationMessage:
    channel: NotificationChannel
    recipient: str
    subject: str
    body: str
    metadata: dict = field(default_factory=dict)


class BaseNotificationProvider(ABC):
    """Contract that future WhatsApp Business API, SMS, and Email gateways must implement."""

    channel: NotificationChannel

    @abstractmethod
    def send(self, message: NotificationMessage) -> dict:
        """Dispatch a message and return a provider status dictionary."""
        raise NotImplementedError
