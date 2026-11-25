import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("havells_sambandh")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "expire-overdue-confirmation-links-every-15-min": {
        "task": "apps.notifications.tasks.expire_overdue_confirmation_links",
        "schedule": crontab(minute="*/15"),
    },
}
