from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.generics import ListAPIView, UpdateAPIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from account.utils import UserListPaginationClass
from account.serializers import (LoginSerializer, UserUpdateSerializer, UserListSerializer, 
                                 RegistrationSerializer, RoleSerializer, MenuWithSubmenusSerializer, MenuRecursiveSerializer)
from account.models import User, Role, Menu, Role, RoleMenuPermission


class RegistrationAPIView(APIView):
    permission_classes = [AllowAny]  # Allow anyone to access registration

    def post(self, request, *args, **kwargs):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"message": "User registered successfully.", "user_id": user.id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# API for User Login
class LoginAPIView(APIView):
    permission_classes = [AllowAny]  # Allow anyone to access this view

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# API for Updating User Details
class UserUpdateAPIView(UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Allow users to update their own profile only
        return self.queryset.filter(id=self.request.user.id)


class UserListAPIView(ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    serializer_class = UserListSerializer
    pagination_class = UserListPaginationClass
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    # Searchable fields
    search_fields = ['name', 'email', 'phone', 'roles__name']
    # Filterable fields (exact, icontains match)
    filterset_fields = {
        'name': ['exact', 'icontains'],
        'email': ['exact', 'icontains'],
        'phone': ['exact', 'icontains'],
        'roles__name': ['exact'],
    }
    # Ordering fields
    ordering_fields = ['name', 'roles__name']
    ordering = ['name']  # Default ordering
   
    def get_queryset(self):
        queryset = User.objects.prefetch_related('roles').filter(is_active=True)
        return queryset


class RoleListAPIView(ListAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]


class RoleMenuPermissionListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            role = request.user.role
        except Role.DoesNotExist:
            return Response({"detail": "Role not found."}, status=404)
        
        # Only top-level menus assigned to this role
        menu_ids = RoleMenuPermission.objects.filter(role=role, menu__parent__isnull=True).values_list('menu_id', flat=True)
        menus = Menu.objects.filter(id__in=menu_ids).order_by('order', 'id').prefetch_related('submenus')
        serializer = MenuWithSubmenusSerializer(menus, many=True, context={'role': role})
        return Response(serializer.data)
    

class RoleMenuPermissionNestedListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            role = request.user.role
        except Role.DoesNotExist:
            return Response({"detail": "Role not found."}, status=404)
        
        # Only top-level menus assigned to this role
        menu_ids = RoleMenuPermission.objects.filter(role=role, menu__parent__isnull=True).values_list('menu_id', flat=True)
        menus = Menu.objects.filter(id__in=menu_ids).order_by('order', 'id').prefetch_related('submenus')
        serializer = MenuRecursiveSerializer(menus, many=True, context={'role': role})
        return Response(serializer.data)
    
