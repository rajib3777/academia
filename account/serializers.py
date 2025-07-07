from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import make_password

from account.choices import CONFLICT_ROLE_PAIRS
from account.models import User, Role
from account.utils import get_or_update_role_cache
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
    user_id = serializers.IntegerField(read_only=True)
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
        attrs['user_id'] = user.id
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
