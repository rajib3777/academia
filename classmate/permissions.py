from rest_framework.permissions import BasePermission

class IsTeacher(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_teacher()


class IsAcademyOwner(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_academy_owner()
