"""Celery background tasks for Havells Sambandh automation workflows."""
from celery import shared_task
from django.utils import timezone

from apps.audit_logs.services import log_audit_event
from apps.confirmations.models import ConfirmationLink, ConfirmationLinkStatus
from apps.notifications.providers.base import NotificationChannel
from apps.notifications.services import dispatch_notification, on_link_expired


@shared_task(name="apps.notifications.tasks.expire_overdue_confirmation_links")
def expire_overdue_confirmation_links() -> int:
    """Periodic Celery task marking overdue active/shared links as expired."""
    now = timezone.now()
    overdue_qs = ConfirmationLink.objects.filter(
        status__in=[ConfirmationLinkStatus.ACTIVE, ConfirmationLinkStatus.SHARED],
        expires_at__lt=now,
    )
    expired_count = overdue_qs.update(
        status=ConfirmationLinkStatus.EXPIRED,
        updated_at=now,
    )
    if expired_count > 0:
        log_audit_event(
            user=None,
            action="LINKS_EXPIRED_SWEEP",
            module="confirmations",
            object_type="ConfirmationLink",
            new_values={"expired_count": expired_count},
        )
        on_link_expired(expired_count=expired_count)
    return expired_count


@shared_task(name="apps.notifications.tasks.send_notification_async")
def send_notification_async(
    channel: str,
    recipient: str,
    subject: str,
    body: str,
    metadata: dict | None = None,
) -> dict:
    return dispatch_notification(
        channel=NotificationChannel(channel),
        recipient=recipient,
        subject=subject,
        body=body,
        metadata=metadata,
    )
