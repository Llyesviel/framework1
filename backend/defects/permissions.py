from rest_framework.permissions import BasePermission

class DefectPermission(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_manager:
            return True
        if user.is_engineer:
            if request.method in ("GET", "HEAD", "OPTIONS"):
                return True
            return obj.performer_id == user.id
        if user.is_observer:
            return request.method in ("GET", "HEAD", "OPTIONS")
        return False