from rest_framework.permissions import BasePermission

class IsManager(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_manager)

class IsEngineer(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_engineer)

class IsObserver(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_observer)

class ManagerOrOwnerEngineer(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_manager:
            return True
        if request.user.is_engineer:
            return getattr(obj, "performer_id", None) == request.user.id
        return False