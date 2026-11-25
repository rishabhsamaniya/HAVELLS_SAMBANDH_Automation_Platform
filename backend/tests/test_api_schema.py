"""Automated tests for Phase 15: Health Check & OpenAPI 3.0 Schema endpoints."""
from django.urls import reverse
import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestAPIDocumentationAndHealth:
    def test_health_and_openapi_schema_endpoints_return_200(self):
        client = APIClient()

        health = client.get(reverse("health-check"))
        assert health.status_code == 200
        assert health.json()["success"] is True

        schema = client.get(reverse("schema"))
        assert schema.status_code == 200
        assert b"Havells Sambandh API" in schema.content

        swagger = client.get(reverse("swagger-ui"))
        assert swagger.status_code == 200
