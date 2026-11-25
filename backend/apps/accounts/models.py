"""Custom User model using 10-digit Indian mobile number as primary identifier."""
import uuid

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone

from common.validators.mobile import normalize_indian_mobile, validate_indian_mobile


class UserManager(BaseUserManager):
    """Manager for custom User model authenticated by mobile_number."""

    def create_user(
        self,
        mobile_number: str,
        full_name: str,
        password: str | None = None,
        **extra_fields,
    ):
        if not mobile_number:
            raise ValueError("Mobile number is required.")
        if not full_name:
            raise ValueError("Full name is required.")

        normalized_mobile = normalize_indian_mobile(mobile_number)
        validate_indian_mobile(normalized_mobile)

        email = extra_fields.pop("email", None)
        if email:
            email = self.normalize_email(email)

        user = self.model(
            mobile_number=normalized_mobile,
            full_name=full_name.strip(),
            email=email,
            **extra_fields,
        )
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        mobile_number: str,
        full_name: str,
        password: str,
        **extra_fields,
    ):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(
            mobile_number=mobile_number,
            full_name=full_name,
            password=password,
            **extra_fields,
        )


class User(AbstractBaseUser, PermissionsMixin):
    """Enterprise internal user authenticated via mobile_number + password."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=150)
    mobile_number = models.CharField(
        max_length=15,
        unique=True,
        validators=[validate_indian_mobile],
        db_index=True,
    )
    email = models.EmailField(blank=True, null=True)
    reporting_manager = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="direct_reports",
    )
    is_active = models.BooleanField(default=True, db_index=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "mobile_number"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        db_table = "accounts_user"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active", "created_at"], name="idx_user_active_created"),
        ]

    def save(self, *args, **kwargs):
        self.mobile_number = normalize_indian_mobile(self.mobile_number)
        if self.email:
            self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.full_name} ({self.mobile_number})"
