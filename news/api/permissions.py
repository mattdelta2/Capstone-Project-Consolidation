from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    - SAFE_METHODS: always allowed
    - POST: only authenticated staff or users in "Journalist" group
    - PUT/PATCH/DELETE: only staff, "Editor" group, or the object's author (journalist)
    """

    def has_permission(self, request, view):
        # Allow anyone to read
        if request.method in permissions.SAFE_METHODS:
            return True

        # All write operations require authentication
        if not request.user or not request.user.is_authenticated:
            return False

        # Only staff or journalists can create articles
        if request.method == 'POST':
            return (
                request.user.is_staff
                or request.user.groups.filter(name="Journalist").exists()
            )

        # For PUT/PATCH/DELETE, defer to has_object_permission
        return True

    def has_object_permission(self, request, view, obj):
        # Always allow reads
        if request.method in permissions.SAFE_METHODS:
            return True

        # Staff or users in "Editor" group can modify any article
        if request.user.is_staff or request.user.groups.filter(name="Editor").exists():
            return True

        # Journalists can modify their own articles
        # Make sure this matches the field on your Article model:
        return obj.author == request.user
