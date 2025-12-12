from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.generics import ListAPIView, UpdateAPIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from account.utils import UserListPaginationClass, generate_otp
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.core.exceptions import PermissionDenied
from datetime import timedelta, datetime
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.conf import settings
from rest_framework.decorators import action, api_view, permission_classes
from account.serializers import (LoginSerializer, UserUpdateSerializer, UserListSerializer, 
                                 RegistrationSerializer, RoleSerializer, MenuWithSubmenusSerializer, MenuRecursiveSerializer)
from account.models import User, Role, Menu, Role, RoleMenuPermission, RecoveryOTP


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



class GenerateRecoveryOTPAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication, BasicAuthentication]
    
    def get(self, request):
        # super admin check
        if not request.user.is_superuser and not request.user.is_admin():
            raise PermissionDenied("Only super-admins can generate OTP.")

        academy_id = request.GET.get("academy_id")
        if not academy_id:
            return JsonResponse({"error": "academy_id is required"}, status=400)

        try:
            from academy.models import Academy
            academy = Academy.objects.get(academy_id=academy_id)
            target_user = academy.user
        except Academy.DoesNotExist:
            return JsonResponse({"error": "academy not found"}, status=404)

        # Set expiry to end of this year
        now = timezone.now()
        current_year = now.year
        expires_at = timezone.make_aware(datetime(current_year, 12, 31, 23, 59, 59))

        for _ in range(50):
            otp_code = generate_otp()
            otp_obj = RecoveryOTP.objects.create(
                user=target_user,
                code=otp_code,
                expires_at=expires_at,
                created_by=request.user,
                status="not_used"
            )

        return JsonResponse({
            "message": "OTP generated successfully",
            "user": target_user.username
        })


def cookie_login_view(request):
    phone = request.data.get("phone")
    password = request.data.get("password")

    user = authenticate(username=phone, password=password)
    if not user:
        return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    response = Response({"success": True}, status=status.HTTP_200_OK)

    # -------------------------
    # SET CROSS-DOMAIN COOKIE
    # -------------------------
    response.set_cookie(
        key="access",
        value=access_token,
        max_age=24 * 60 * 60,
        secure=True,
        httponly=True,
        samesite="None",
        domain=".classmatespro.com",    # IMPORTANT!
    )

    response.set_cookie(
        key="refresh",
        value=str(refresh),
        max_age=7 * 24 * 60 * 60,
        secure=True,
        httponly=True,
        samesite="None",
        domain=".classmatespro.com",
    )

    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user
    refresh = RefreshToken.for_user(user)

    return Response({
        "userID": user.id,
        "name": user.get_full_name(),
        "username": user.username,
        "phone": user.phone,
        "role": user.role.name,
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    })
