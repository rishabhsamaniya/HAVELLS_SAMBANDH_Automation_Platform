"""Default non-blocking log/stub providers used until external gateways are configured."""
import logging

from apps.notifications.providers.base import (
    BaseNotificationProvider,
    NotificationChannel,
    NotificationMessage,
)

logger = logging.getLogger(__name__)


class _BaseLogProvider(BaseNotificationProvider):
    def send(self, message: NotificationMessage) -> dict:
        logger.info(
            "[NOTIFICATION:%s] to=%s subject=%s",
            self.channel.value,
            message.recipient,
            message.subject,
        )
        return {
            "delivered": True,
            "provider": self.__class__.__name__,
            "channel": self.channel.value,
        }


class LogWhatsAppProvider(_BaseLogProvider):
    channel = NotificationChannel.WHATSAPP


class LogSMSProvider(_BaseLogProvider):
    channel = NotificationChannel.SMS


class LogEmailProvider(_BaseLogProvider):
    channel = NotificationChannel.EMAIL


class InAppNotificationProvider(_BaseLogProvider):
    channel = NotificationChannel.IN_APP
