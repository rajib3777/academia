from rest_framework import serializers
from .models import Academy, Course, Batch


class BatchSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Batch
        fields = ['id', 'name', 'start_date', 'end_date']
        read_only_fields = ['id']


class CourseSerializer(serializers.ModelSerializer):
    batches = BatchSerializer(many=True)

    class Meta:
        model = Course
        fields = ['id', 'name', 'description', 'fee', 'batches']
        read_only_fields = ['id']

    def create(self, validated_data):
        batches_data = validated_data.pop('batches', [])
        course = Course.objects.create(**validated_data)

        for batch_data in batches_data:
            Batch.objects.create(course=course, **batch_data)

        return course
    
    def update(self, instance, validated_data):
        batches_data = validated_data.pop('batches', [])

        if batches_data is not None:
            incoming_batch_ids = [b.get('id') for b in batches_data if b.get('id') is not None]
            
            # Delete batches not in incoming data
            for batch in instance.batches.all():
                if batch.id not in incoming_batch_ids:
                    batch.delete()

            # Create or update batches
            for batch_data in batches_data:
                batch_id = batch_data.get('id')
                if batch_id:  # Update
                    try:
                        batch = instance.batches.get(id=batch_id)
                        for attr, value in batch_data.items():
                            setattr(batch, attr, value)
                        batch.save()
                    except Batch.DoesNotExist:
                        continue  # or raise an error if you prefer
                else:  # Create
                    Batch.objects.create(course=instance, **batch_data)

        # Update course fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


class AcademySerializer(serializers.ModelSerializer):
    # courses = serializers.PrimaryKeyRelatedField(many=True, queryset=Course.objects.all())
    # courses = serializers.PrimaryKeyRelatedField(many=True, queryset=Course.objects.all(), write_only=True)
    courses = CourseSerializer(many=True, read_only=True)
    class Meta:
        model = Academy
        fields = ['id', 'name', 'description', 'logo', 'website', 'contact_number', 'email', 'owner', 'courses']
        read_only_fields = ['id',]


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