from rest_framework import serializers
from django.db import transaction
from .models import Academy, Course, Batch
from account.serializers import UserSerializer

class BatchSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Batch
        fields = ['id', 'name', 'course', 'start_date', 'end_date', 'is_active', 'description']
        read_only_fields = ['id']


class BatchCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Batch
        fields = ['id', 'name', 'start_date', 'end_date', 'is_active', 'description']
        read_only_fields = ['id']

    def validate(self, attrs):
        name = attrs.get('name')
        course = attrs.get('course')
        
        request = self.context.get('request')

        academy = request.user.academy.first()

        if not academy:
            raise serializers.ValidationError({"academy": "No academy is associated with this user."})

        if self.instance:
            # For update – skip if the name and course aren't changed
            if (self.instance.name == name and self.instance.course == course):
                return attrs

        if Batch.objects.filter(name=name, course_id=course, course__academy=academy).exists():
            raise serializers.ValidationError({
                'name': 'A batch with this name already exists for the selected course.'
            })

        return attrs


class CourseSerializer(serializers.ModelSerializer):
    batches = BatchSerializer(many=True)

    class Meta:
        model = Course
        fields = ['id', 'name', 'description', 'fee', 'batches']
        read_only_fields = ['id']

class CourseCreateSerializer(serializers.ModelSerializer):
    batches = BatchCreateSerializer(many=True)

    class Meta:
        model = Course
        fields = ['id', 'name', 'description', 'fee', 'batches']
        read_only_fields = ['id']

    def validate(self, attrs):
        name = attrs.get('name')
        
        request = self.context.get('request')

        academy = request.user.academy.first()

        if not academy:
            raise serializers.ValidationError({"academy": "No academy is associated with this user."})

        if self.instance:
            # For update – skip if the name and course aren't changed
            if (self.instance.name == name and self.instance.academy == academy):
                return attrs
        
        if Course.objects.filter(academy=academy, name=name).exists():
            raise serializers.ValidationError({
                'name': 'This course name already exists for this academy.'
            })

        return attrs


    def create(self, validated_data):
        batches_data = validated_data.pop('batches', [])
        course = Course.objects.create(**validated_data)
        print('course: ', course)
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
    user = UserSerializer()
    class Meta:
        model = Academy
        fields = ['id', 'name', 'description', 'established_year', 'logo', 'website', 'contact_number', 'email', 'user', 
                  'division', 'district', 'upazila', 'area_or_union', 'street_address', 'postal_code', 'courses']
        read_only_fields = ['id',]


    def validate_name(self, value):
        # Check if the name already exists for a different academy
        academy_id = self.instance.id if self.instance else None
        if Academy.objects.exclude(id=academy_id).filter(name__iexact=value).exists():
            raise serializers.ValidationError("Academy with this name already exists.")
        return value
    
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        print('in: ', user_data)
        with transaction.atomic():
            user_serializer = UserSerializer()
            user = user_serializer.create(user_data)
            academy = Academy.objects.create(user=user, **validated_data)
            return academy
        
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        print('user: ', user_data)
        with transaction.atomic():
            # Update user if user data is provided
            if user_data:
                user_serializer = UserSerializer(instance.user, data=user_data, partial=True)
                if user_serializer.is_valid(raise_exception=True):
                    user_serializer.save()
            
            # Update academy fields
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            
            instance.save()
            return instance
    

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


class BatchNameListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Batch
        fields = ['id', 'name']