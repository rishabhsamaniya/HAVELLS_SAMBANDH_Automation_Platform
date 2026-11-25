from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


admin.site.site_header = "Havells Sambandh Administration"
admin.site.site_title = "Havells Sambandh Admin"
admin.site.index_title = "Platform Management"


def health_check(request):
    return JsonResponse(
        {
            "success": True,
            "message": "Havells Sambandh API is healthy.",
            "data": {"status": "ok"},
        }
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health/", health_check, name="health-check"),
    # OpenAPI / Swagger Documentation
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/v1/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # Domain API routes (activated progressively in Phases 05-15)
    path("api/v1/auth/", include("apps.accounts.urls_auth")),
    path("api/v1/users/", include("apps.accounts.urls_users")),
    path("api/v1/roles/", include("apps.roles.urls")),
    path("api/v1/permissions/", include("apps.permissions.urls")),
    path("api/v1/dealers/", include("apps.dealers.urls")),
    path("api/v1/campaigns/", include("apps.campaigns.urls")),
    path("api/v1/confirmation-links/", include("apps.confirmations.urls_links")),
    path("api/v1/public/confirm/", include("apps.confirmations.urls_public")),
    path("api/v1/scheduling/", include("apps.scheduling.urls")),
    path("api/v1/dashboard/", include("apps.dashboard.urls")),
    path("api/v1/reports/", include("apps.reports.urls")),
    path("api/v1/audit-logs/", include("apps.audit_logs.urls")),
]
