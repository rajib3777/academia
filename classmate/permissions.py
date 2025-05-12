from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import PermissionDenied


class IsTeacher(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_teacher()


class IsAdminOrAcademyOwner(BasePermission):
    """
    Only users with role 'admin' or 'academy' can access.
    """

    def has_permission(self, request, view):
        user = request.user
        return (
            user.is_authenticated and
            (user.is_superuser or user.is_admin() or user.is_academy_owner())
        )
    

class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_student()


class IsAcademyOwnerAndOwnsObjectOrAdmin(BasePermission):
    """
    Allow object-level access only if:
    - user is admin
    - or user is academy owner and owns the object (obj.user == request.user or academy.user == request.user)
    """

    def has_object_permission(self, request, view, obj):
        user = request.user

        if not user.is_authenticated:
            return False

        # Admins can access everything
        if user.is_superuser or user.is_admin():
            return True

        # For Academy
        if hasattr(obj, 'user'):
            return obj.user == user

        # For Course
        if hasattr(obj, 'academy'):
            return obj.academy.user == user

        # For Batch
        if hasattr(obj, 'course'):
            return obj.course.academy.user == user

        return False


class IsAcademyOwner(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        return (
            user.is_authenticated and user.is_academy_owner()
        )
    

class IsSuperUserOrAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            raise PermissionDenied(detail="Authentication credentials were not provided.")

        if not (user.is_superuser or user.is_admin()):
            raise PermissionDenied(detail="You don't have permission")

        return True
    

class AuthenticatedGenericView:
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication, BasicAuthentication, TokenAuthentication, JWTAuthentication]