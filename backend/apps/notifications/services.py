"""Notification dispatcher and lifecycle automation workflow hooks."""
import logging

from apps.notifications.providers.base import (
    BaseNotificationProvider,
    NotificationChannel,
    NotificationMessage,
)
from apps.notifications.providers.stubs import (
    InAppNotificationProvider,
    LogEmailProvider,
    LogSMSProvider,
    LogWhatsAppProvider,
)

logger = logging.getLogger(__name__)

_PROVIDER_REGISTRY: dict[NotificationChannel, BaseNotificationProvider] = {
    NotificationChannel.WHATSAPP: LogWhatsAppProvider(),
    NotificationChannel.SMS: LogSMSProvider(),
    NotificationChannel.EMAIL: LogEmailProvider(),
    NotificationChannel.IN_APP: InAppNotificationProvider(),
}


def get_provider(channel: NotificationChannel) -> BaseNotificationProvider:
    return _PROVIDER_REGISTRY[channel]


def dispatch_notification(
    *,
    channel: NotificationChannel,
    recipient: str,
    subject: str,
    body: str,
    metadata: dict | None = None,
) -> dict:
    provider = get_provider(channel)
    message = NotificationMessage(
        channel=channel,
        recipient=recipient,
        subject=subject,
        body=body,
        metadata=metadata or {},
    )
    return provider.send(message)


# --- Automation Lifecycle Hooks ---

def on_link_generated(*, link, share_message: str) -> dict:
    """Hook: Link Generated (prepares/logs shareable dealer outreach event)."""
    return dispatch_notification(
        channel=NotificationChannel.IN_APP,
        recipient=link.assigned_rm.mobile_number,
        subject=f"Confirmation Link Ready: {link.dealer.dealer_code}",
        body=share_message,
        metadata={"event": "LINK_GENERATED", "dealer_code": link.dealer.dealer_code},
    )


def on_link_shared(*, link) -> dict:
    """Hook: Link Shared."""
    return dispatch_notification(
        channel=NotificationChannel.IN_APP,
        recipient=link.assigned_rm.mobile_number,
        subject=f"Link Shared: {link.dealer.dealer_code}",
        body=f"Confirmation link for dealer {link.dealer.dealer_code} marked as shared.",
        metadata={"event": "LINK_SHARED", "dealer_code": link.dealer.dealer_code},
    )


def on_form_submitted(*, confirmation) -> dict:
    """Hook: Dealer Confirmation Form Submitted."""
    return dispatch_notification(
        channel=NotificationChannel.IN_APP,
        recipient=confirmation.dealer.assigned_rm.mobile_number,
        subject=f"Confirmation Received: {confirmation.dealer.dealer_code}",
        body=(
            f"Dealer {confirmation.dealer.dealer_code} confirmed "
            f"{confirmation.preferred_date.isoformat()} ({confirmation.preferred_time_slot.display_label})."
        ),
        metadata={"event": "FORM_SUBMITTED", "confirmation_id": str(confirmation.id)},
    )


def on_link_expired(*, expired_count: int) -> dict:
    """Hook: Scheduled Link Expiration Sweep."""
    logger.info("[AUTOMATION:LINK_EXPIRED] Marked %d overdue confirmation links as expired.", expired_count)
    return {"event": "LINK_EXPIRED", "expired_count": expired_count}


def on_booking_changed(*, confirmation, action: str, reason: str = "") -> dict:
    """Hook: Booking Rescheduled or Cancelled — notifies assigned RM."""
    return dispatch_notification(
        channel=NotificationChannel.IN_APP,
        recipient=confirmation.dealer.assigned_rm.mobile_number,
        subject=f"Booking {action.title()}: {confirmation.dealer.dealer_code}",
        body=(
            f"Booking for dealer {confirmation.dealer.dealer_code} was {action}. "
            f"Date: {confirmation.preferred_date.isoformat()} ({confirmation.preferred_time_slot.display_label}). "
            f"Reason: {reason or 'N/A'}"
        ),
        metadata={"event": "BOOKING_CHANGED", "action": action, "confirmation_id": str(confirmation.id)},
    )
