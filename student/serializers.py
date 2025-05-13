from rest_framework import serializers
from student.models import School

class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = '__all__'

    def validate_name(self, value):
        # For create
        if self.instance is None and School.objects.filter(name=value).exists():
            raise serializers.ValidationError("A school with this name already exists.")
        
        # For update
        if self.instance and School.objects.filter(name=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("Another school with this name already exists.")
        
        return value