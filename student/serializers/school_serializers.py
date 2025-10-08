from rest_framework import serializers
from student.models import School

class SchoolCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    address = serializers.CharField()
    email = serializers.EmailField(required=False, allow_blank=True)
    contact_number = serializers.CharField(max_length=15, required=False, allow_blank=True)
    website = serializers.URLField(required=False, allow_blank=True)
    logo = serializers.ImageField(required=False, allow_null=True)

    def validate_name(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError('School name cannot be empty.')
    
        # For create
        if self.instance is None and School.objects.filter(name=value).exists():
            raise serializers.ValidationError('A school with this name already exists.')
        return value

class SchoolUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, max_length=255)
    address = serializers.CharField(required=False)
    email = serializers.EmailField(required=False, allow_blank=True)
    contact_number = serializers.CharField(max_length=15, required=False, allow_blank=True)
    website = serializers.URLField(required=False, allow_blank=True)
    logo = serializers.ImageField(required=False, allow_null=True)

    def validate_name(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError('School name cannot be empty.')
        # For update
        if self.instance and School.objects.filter(name=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError('Another school with this name already exists.')
        return value

class SchoolDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    address = serializers.CharField()
    email = serializers.EmailField(allow_blank=True)
    contact_number = serializers.CharField(allow_blank=True)
    website = serializers.URLField(allow_blank=True)
    logo = serializers.ImageField(allow_null=True)

class SchoolListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    address = serializers.CharField()
    email = serializers.EmailField(allow_blank=True)
    contact_number = serializers.CharField(allow_blank=True)
    website = serializers.URLField(allow_blank=True)
    logo = serializers.ImageField(allow_null=True)

    def get_logo(self, obj) -> str:
        print('obj:', obj, obj.logo)
        request = self.context.get('request')
        if obj.logo and hasattr(obj.logo, 'url'):
            url = obj.logo.url
            if request is not None:
                return request.build_absolute_uri(url)
            return url
        return None