from rest_framework import serializers
from utils.models import Division, District, Upazila


class SendOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)

class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)


# https://chatgpt.com/c/67968737-06d4-8010-ae46-b284984da583

class DivisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Division
        fields = ['id', 'name']


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ['id', 'name', 'division']


class UpazilaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Upazila
        fields = ['id', 'name', 'district']
