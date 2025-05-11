from rest_framework import serializers
from .models import Academy, Course, Batch


class BatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Batch
        fields = ['id', 'name', 'course', 'start_date', 'end_date']
        read_only_fields = ['id']


class CourseSerializer(serializers.ModelSerializer):
    batches = BatchSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'name', 'description', 'fee', 'batches']
        read_only_fields = ['id']


class AcademySerializer(serializers.ModelSerializer):
    # courses = serializers.PrimaryKeyRelatedField(many=True, queryset=Course.objects.all())
    # courses = serializers.PrimaryKeyRelatedField(many=True, queryset=Course.objects.all(), write_only=True)
    courses = CourseSerializer(many=True, read_only=True)
    class Meta:
        model = Academy
        fields = ['id', 'name', 'description', 'logo', 'website', 'address', 'contact_number', 'email', 'owner', 'courses']
        read_only_fields = ['id', 'owner']


    def validate_name(self, value):
        # Check if the name already exists for a different academy
        academy_id = self.instance.id if self.instance else None
        if Academy.objects.exclude(id=academy_id).filter(name__iexact=value).exists():
            raise serializers.ValidationError("Academy with this name already exists.")
        return value
    

class AcademyOwnerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Academy
        fields = ['name', 'description', 'logo', 'website', 'contact_number', 'email',]


    def validate_name(self, value):
        # Check if the name already exists for a different academy
        academy_id = self.instance.id if self.instance else None
        if Academy.objects.exclude(id=academy_id).filter(name__iexact=value).exists():
            raise serializers.ValidationError("Academy with this name already exists.")
        return value
    

class CourseNameListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'name']