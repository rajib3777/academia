from rest_framework import serializers
from landingpage.models import (
    AcademyGallery, 
    AcademyFacility, 
    AcademyProgram,
    AcademyReview,

)

from academy.models import (
    Academy, 
    Course,
    Batch,
    BatchEnrollment
)
from utils.serializers import DivisionSerializer, DistrictSerializer, UpazilaSerializer


class AcademyProgramSerializer(serializers.ModelSerializer):
    """Serializer for academy programs"""
    
    class Meta:
        model = AcademyProgram
        fields = ['id', 'name']

class FeaturedAcademySerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    short_description = serializers.CharField(read_only=True)
    featured_image = serializers.ImageField(read_only=True)
    featured_subject = serializers.SerializerMethodField()
    logo = serializers.ImageField(read_only=True)
    location = serializers.SerializerMethodField()
    total_students = serializers.IntegerField(read_only=True)
    average_rating = serializers.DecimalField(
        max_digits=2, 
        decimal_places=1, 
        read_only=True
    )
    review_count = serializers.IntegerField(read_only=True)
    # programs = AcademyProgramSerializer(many=True, read_only=True)
    established_year = serializers.CharField(read_only=True)

    def get_featured_subject(self, obj):
        return obj.get_featured_subject_display() if obj.featured_subject else None
    
    def get_location(self, obj):
        location_parts = []
        if obj.district:
            location_parts.append(obj.district.name)
        if obj.division:
            location_parts.append(obj.division.name)
        return ", ".join(location_parts) if location_parts else "N/A"
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        if data.get('average_rating') is None:
            data['average_rating'] = 0.0
        
        # Format rating to 1 decimal place
        if data.get('average_rating'):
            data['average_rating'] = round(float(data['average_rating']), 1)
        
        return data


class AcademyGallerySerializer(serializers.ModelSerializer):
    """Serializer for academy gallery images"""
    
    class Meta:
        model = AcademyGallery
        fields = ['id', 'image', 'title', 'description', 'order']


class AcademyFacilitySerializer(serializers.ModelSerializer):
    """Serializer for academy facilities"""
    
    class Meta:
        model = AcademyFacility
        fields = ['id', 'name' ]


class AcademyReviewSerializer(serializers.ModelSerializer):
    """Serializer for academy reviews"""
    reviewer_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = AcademyReview
        fields = [
            'id', 
            'reviewer_name', 
            'rating', 
            'review_text', 
            'is_verified',
            'created_at'
        ]

class BatchInCourseSerializer(serializers.ModelSerializer):
    """Serializer for batches within courses"""
    enrolled_students = serializers.SerializerMethodField()
    
    class Meta:
        model = Batch
        fields = [
            'id', 
            'name', 
            'start_date', 
            'end_date', 
            'is_active',
            'enrolled_students'
        ]
    
    def get_enrolled_students(self, obj):
        """Get count of enrolled students"""
        return obj.students.filter(
            batchenrollment__is_active=True
        ).count()

class CourseInAcademySerializer(serializers.ModelSerializer):
    """Serializer for courses within academy details"""
    batches = BatchInCourseSerializer(many=True, read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'id',
            'name',
            'description',
            'fee',
            'subject',
            'batches'
        ]

class AcademyDetailSerializer(serializers.Serializer):
    """
    Detailed serializer for academy details page.
    Includes all information needed for the details view.
    """
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    short_description = serializers.CharField(read_only=True)
    logo = serializers.ImageField(read_only=True)
    cover_image = serializers.ImageField(read_only=True)
    featured_image = serializers.ImageField(read_only=True)
    website = serializers.URLField(read_only=True)
    contact_number = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    established_year = serializers.CharField(read_only=True)
    
    # Location
    division = DivisionSerializer(read_only=True)
    district = DistrictSerializer(read_only=True)
    upazila = UpazilaSerializer(read_only=True)
    area_or_union = serializers.CharField(read_only=True)
    street_address = serializers.CharField(read_only=True)
    postal_code = serializers.CharField(read_only=True)
    full_address = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    
    # Stats
    total_students = serializers.IntegerField(read_only=True)
    average_rating = serializers.DecimalField(
        max_digits=2, 
        decimal_places=1, 
        read_only=True
    )
    review_count = serializers.IntegerField(read_only=True)
    
    # Related data
    programs = AcademyProgramSerializer(many=True, read_only=True)
    facilities = AcademyFacilitySerializer(many=True, read_only=True)
    gallery_images = AcademyGallerySerializer(many=True, read_only=True)
    reviews = AcademyReviewSerializer(many=True, read_only=True)
    courses = CourseInAcademySerializer(many=True, read_only=True)
    
    def get_full_address(self, obj):
        """Get formatted full address"""
        address_parts = []
        if obj.street_address:
            address_parts.append(obj.street_address)
        if obj.area_or_union:
            address_parts.append(obj.area_or_union)
        if obj.upazila:
            address_parts.append(obj.upazila.name)
        if obj.district:
            address_parts.append(obj.district.name)
        if obj.division:
            address_parts.append(obj.division.name)
        if obj.postal_code:
            address_parts.append(obj.postal_code)
        
        return ", ".join(address_parts) if address_parts else "N/A"
    
    def get_location(self, obj):
        """Get short location string"""
        location_parts = []
        if obj.district:
            location_parts.append(obj.district.name)
        if obj.division:
            location_parts.append(obj.division.name)
        return ", ".join(location_parts) if location_parts else "N/A"

    def get_reviews(self, obj):
        """Get latest reviews"""
        reviews = getattr(obj, 'latest_reviews', [])
        return AcademyReviewSerializer(reviews, many=True).data
    
    def to_representation(self, instance):
        """Custom representation"""
        data = super().to_representation(instance)
        
        # Handle None values for ratings
        if data.get('average_rating') is None:
            data['average_rating'] = 0.0
        
        # Format rating to 1 decimal place
        if data.get('average_rating'):
            data['average_rating'] = round(float(data['average_rating']), 1)
        
        return data

class ProgramFilterSerializer(serializers.Serializer):
    """Serializer for program filter options"""
    name = serializers.CharField()
