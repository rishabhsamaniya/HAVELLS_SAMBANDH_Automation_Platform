"""DRF permission classes backed by the centralized PermissionService."""
from rest_framework.permissions import BasePermission

from apps.permissions.services import PermissionService


class HasModulePermission(BasePermission):
    """
    Checks dynamic module.action permissions defined on the view via:
    - `required_permission = "module.action"` (applies to all methods), OR
    - `method_permissions = {"GET": "module.view", "POST": "module.add", ...}`
      (values may be a single codename str or a tuple/list of codenames where any suffices).
    """

    message = "You do not have permission to perform this action."

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated or not user.is_active:
            return False

        method_map = getattr(view, "method_permissions", None)
        if isinstance(method_map, dict) and request.method in method_map:
            required = method_map[request.method]
        else:
            required = getattr(view, "required_permission", None)

        if not required:
            return True

        if isinstance(required, (list, tuple, set)):
            return PermissionService.has_any_permission(user, list(required))
        return PermissionService.has_permission(user, required)
