from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import make_password
from account.choices import CONFLICT_ROLE_PAIRS
from account.services.user_service import UserService
from account.selectors.user_selector import UserSelector
from account.models import User, Role, Menu, Permission, RoleMenuPermission
from account.utils import get_or_update_role_cache, generate_secure_password
from utils.models import OTPVerification


class RegistrationSerializer(serializers.ModelSerializer):
    roles = serializers.ListField(child=serializers.CharField(), write_only=True)

    class Meta:
        model = User
        fields = ['name', 'email', 'phone', 'password', 'roles']
        extra_kwargs = {
            'password': {'write_only': True},  # Ensure password is write-only
        }

    def validate_phone(self, value):
        # Check if the phone number is associated with a verified OTP
        try:
            otp_record = OTPVerification.objects.get(phone_number=value)
            if not otp_record.is_verified:
                raise serializers.ValidationError("Phone number is not verified.")
            if otp_record.is_expired():
                raise serializers.ValidationError("OTP for this phone number has expired. Please request a new OTP.")
        except OTPVerification.DoesNotExist:
            raise serializers.ValidationError("Phone number has not been verified. Please verify your phone number first.")
        return value

    def validate_roles(self, roles):
        role_mapping = get_or_update_role_cache() # Fetch role mappings from cache (refresh if expired).
        roles = set(roles[0].lower().split(',')) # Convert a list of comma-separated role strings into a flat set of roles. Set for faster lookup.
        roles.discard('') # remove blank from the set

        # Validate roles
        role_ids = []
        for role in roles:
            if role in role_mapping:
                role_ids.append(role_mapping[role])
            else:
                raise serializers.ValidationError(f"Invalid role: {role}")

        # Conflict role restrictions
        for conflict_roles, error_message in CONFLICT_ROLE_PAIRS:
            if conflict_roles.issubset(set(roles)):
                raise serializers.ValidationError(error_message)

        return role_ids

    def create(self, validated_data):
        """Create a user with hashed password and assigned roles."""
        roles = validated_data.pop("roles", [])  # Get role IDs
        validated_data['password'] = make_password(validated_data['password'])  # Hash the password

        user = User.objects.create(**validated_data)
        user.roles.set(roles)

        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    userID = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    phone = serializers.CharField(read_only=True)
    role = serializers.CharField(read_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError({"error": "User does not exist."})

        if not user.check_password(password):
            raise serializers.ValidationError({"error": "Incorrect password."})

        refresh = RefreshToken.for_user(user)
        attrs['access'] = str(refresh.access_token)
        attrs['refresh'] = str(refresh)
        attrs['userID'] = user.id
        attrs['name'] = user.get_full_name()
        attrs['phone'] = user.phone
        attrs['role'] = user.role.name
        return attrs


# Serializer for updating user details
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'email', 'phone',]


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name']


# Serializer for listing users
class UserListSerializer(serializers.ModelSerializer):
    roles = RoleSerializer(many=True)

    class Meta:
        model = User
        fields = ['id', 'name', 'phone', 'email', 'roles']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'role',]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_service = UserService()
        self.user_selector = UserSelector()

    def create(self, validated_data):
        """
        Create a new user using UserService.
        """
        return self.user_service.create_user(validated_data)
    
    def update(self, instance, validated_data):
        """
        Update user instance using UserService.
        """
        return self.user_service.update_user(instance.id, validated_data)
    
    def validate_email(self, value):
        """
        Validate email uniqueness excluding current instance.
        """
        if self.user_selector.check_email_exists(value, self.instance.pk if self.instance else None):
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_phone(self, value):
        """
        Validate phone uniqueness excluding current instance.
        """
        if self.user_selector.check_phone_exists(value, self.instance.pk if self.instance else None):
            raise serializers.ValidationError("A user with this phone number already exists.")
        return value


# If you want a separate serializer for password updates
class UserPasswordUpdateSerializer(serializers.ModelSerializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['old_password', 'new_password', 'confirm_password']
    
    def validate(self, attrs):
        user = self.instance
        old_password = attrs.get('old_password')
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')
        
        # Check if old password is correct
        if not user.check_password(old_password):
            raise serializers.ValidationError({
                'old_password': 'Old password is incorrect.'
            })
        
        # Check if new passwords match
        if new_password != confirm_password:
            raise serializers.ValidationError({
                'confirm_password': 'New passwords do not match.'
            })
        
        return attrs
    
    def update(self, instance, validated_data):
        new_password = validated_data['new_password']
        instance.set_password(new_password)
        instance.save()
        return instance
    

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['code', ]

class SubMenuSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Menu
        fields = ['name', 'permissions']

    def get_permissions(self, obj):
        role = self.context.get('role')
        if not role:
            return []
        perms = RoleMenuPermission.objects.filter(role=role, menu=obj).first()
        if perms:
            return PermissionSerializer(perms.permissions.all(), many=True).data
        return []

class MenuWithSubmenusSerializer(serializers.ModelSerializer):
    submenus = serializers.SerializerMethodField()
    # permissions = serializers.SerializerMethodField()

    class Meta:
        model = Menu
        # fields = ['name', 'permissions', 'submenus']
        fields = ['name', 'submenus']

    def get_submenus(self, obj):
        role = self.context.get('role')
        # Only submenus assigned to this role
        submenu_ids = RoleMenuPermission.objects.filter(role=role, menu__parent=obj).values_list('menu_id', flat=True)
        submenus = Menu.objects.filter(id__in=submenu_ids).order_by('order', 'id')
        return SubMenuSerializer(submenus, many=True, context={'role': role}).data

    def get_permissions(self, obj):
        role = self.context.get('role')
        perms = RoleMenuPermission.objects.filter(role=role, menu=obj).first()
        if perms:
            return PermissionSerializer(perms.permissions.all(), many=True).data
        return []


class MenuRecursiveSerializer(serializers.ModelSerializer):
    submenus = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Menu
        fields = ['id', 'name', 'order', 'permissions', 'submenus']

    def get_submenus(self, obj):
        role = self.context.get('role')
        # Only submenus assigned to this role, ordered by 'order'
        submenu_ids = RoleMenuPermission.objects.filter(role=role, menu__parent=obj).values_list('menu_id', flat=True)
        submenus = Menu.objects.filter(id__in=submenu_ids).order_by('order', 'id')
        # Recursive call
        return MenuRecursiveSerializer(submenus, many=True, context=self.context).data

    def get_permissions(self, obj):
        role = self.context.get('role')
        perms = RoleMenuPermission.objects.filter(role=role, menu=obj).first()
        if perms:
            return PermissionSerializer(perms.permissions.all(), many=True).data
        return []


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change requests.
    """
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs) -> dict:
        if not attrs.get('old_password') or not attrs.get('new_password') or not attrs.get('confirm_password'):
            raise serializers.ValidationError('All password fields are required.')
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError('New password and confirm password do not match.')
        if len(attrs['new_password']) < 8:
            raise serializers.ValidationError('New password must be at least 8 characters.')
        return attrs