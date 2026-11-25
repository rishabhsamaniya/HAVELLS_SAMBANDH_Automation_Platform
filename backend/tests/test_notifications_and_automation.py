"""Automated tests for Phase 13: Notification Provider Interfaces & Celery Link Expiry Automation."""
from datetime import date, timedelta

from django.utils import timezone
import pytest

from apps.accounts.models import User
from apps.audit_logs.models import AuditLog
from apps.campaigns.models import Campaign
from apps.confirmations.models import ConfirmationLink, ConfirmationLinkStatus
from apps.dealers.models import Dealer
from apps.notifications.providers.base import NotificationChannel
from apps.notifications.services import dispatch_notification
from apps.notifications.tasks import expire_overdue_confirmation_links, send_notification_async
from services.tokens import generate_secure_token, hash_token


@pytest.mark.django_db
class TestNotificationsAndAutomation:
    def test_all_four_notification_provider_interfaces_dispatch_cleanly(self):
        for channel in NotificationChannel:
            result = dispatch_notification(
                channel=channel,
                recipient="9876543210",
                subject="Test Event",
                body="Havells Sambandh notification test",
            )
            assert result["delivered"] is True
            assert result["channel"] == channel.value

        async_res = send_notification_async(
            channel="whatsapp",
            recipient="9876543210",
            subject="Async Test",
            body="Body",
        )
        assert async_res["delivered"] is True

    def test_celery_expire_overdue_links_marks_only_overdue_active_or_shared_links(self):
        rm = User.objects.create_user("9800060001", "RM Auto", "RmPass@123")
        dealer = Dealer.objects.create(dealer_code="AUTO-D1", mobile_number="9876560001", assigned_rm=rm)
        camp = Campaign.objects.create(
            campaign_name="Auto Camp",
            campaign_code="AUTO-2026",
            start_date=date(2026, 11, 1),
            end_date=date(2026, 11, 30),
        )
        now = timezone.now()

        overdue_link = ConfirmationLink.objects.create(
            dealer=dealer,
            token_hash=hash_token(generate_secure_token()),
            campaign=camp,
            assigned_rm=rm,
            allowed_month="2026-11",
            expires_at=now - timedelta(hours=2),
            status=ConfirmationLinkStatus.SHARED,
        )
        future_link = ConfirmationLink.objects.create(
            dealer=dealer,
            token_hash=hash_token(generate_secure_token()),
            campaign=camp,
            assigned_rm=rm,
            allowed_month="2026-11",
            expires_at=now + timedelta(days=3),
            status=ConfirmationLinkStatus.ACTIVE,
        )
        used_link = ConfirmationLink.objects.create(
            dealer=dealer,
            token_hash=hash_token(generate_secure_token()),
            campaign=camp,
            assigned_rm=rm,
            allowed_month="2026-11",
            expires_at=now - timedelta(hours=1),
            status=ConfirmationLinkStatus.USED,
            submission_count=1,
        )

        expired_count = expire_overdue_confirmation_links()
        assert expired_count == 1

        overdue_link.refresh_from_db()
        future_link.refresh_from_db()
        used_link.refresh_from_db()

        assert overdue_link.status == ConfirmationLinkStatus.EXPIRED
        assert future_link.status == ConfirmationLinkStatus.ACTIVE
        assert used_link.status == ConfirmationLinkStatus.USED
        assert AuditLog.objects.filter(action="LINKS_EXPIRED_SWEEP").exists()
