from rest_framework import serializers
from .models import Academy, Course, Batch


class BatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Batch
        fields = '__all__'
        read_only_fields = ['id']


class CourseSerializer(serializers.ModelSerializer):
    batches = BatchSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = '__all__'
        read_only_fields = ['id']


class AcademySerializer(serializers.ModelSerializer):
    # courses = serializers.PrimaryKeyRelatedField(many=True, queryset=Course.objects.all())
    # courses = serializers.PrimaryKeyRelatedField(many=True, queryset=Course.objects.all(), write_only=True)
    courses = CourseSerializer(many=True, read_only=True)
    class Meta:
        model = Academy
        fields = ['id', 'name', 'description', 'logo', 'website', 'address', 'contact_number', 'email', 'owner', 'courses']
        read_only_fields = ['id']