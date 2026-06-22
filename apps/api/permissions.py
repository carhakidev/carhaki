from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """Allow access only to the object's owner."""

    def has_object_permission(self, request, view, obj):
        return hasattr(obj, 'user') and obj.user == request.user
