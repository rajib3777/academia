from rest_framework import serializers
from teacher.models import Teacher
from landingpage.models import TeacherSubject, TeacherEducation, TeacherAchievement, TeacherReview
from academy.models import Academy


class TeacherSubjectSerializer(serializers.ModelSerializer):
    """Serializer for teacher subjects"""
    subject_display = serializers.CharField(source='get_subject_display', read_only=True)
    
    class Meta:
        model = TeacherSubject
        fields = ['id', 'subject', 'subject_display', 'is_primary']


class TeacherEducationSerializer(serializers.ModelSerializer):
    """Serializer for teacher education"""
    
    class Meta:
        model = TeacherEducation
        fields = ['id', 'degree', 'institution', 'year']


class TeacherAchievementSerializer(serializers.ModelSerializer):
    """Serializer for teacher achievements"""
    
    class Meta:
        model = TeacherAchievement
        fields = ['id', 'title', 'description', 'year']


class TeacherReviewSerializer(serializers.ModelSerializer):
    """Serializer for teacher reviews"""
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = TeacherReview
        fields = ['id', 'student_name', 'rating', 'review_text', 'reviewed_at', 'time_ago']
    
    def get_time_ago(self, obj):
        """Calculate time ago from review date"""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        diff = now - obj.reviewed_at
        
        if diff < timedelta(minutes=1):
            return "Just now"
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff < timedelta(days=30):
            days = diff.days
            return f"{days} day{'s' if days > 1 else ''} ago"
        elif diff < timedelta(days=365):
            months = int(diff.days / 30)
            return f"{months} month{'s' if months > 1 else ''} ago"
        else:
            years = int(diff.days / 365)
            return f"{years} year{'s' if years > 1 else ''} ago"


class TeacherCardSerializer(serializers.ModelSerializer):
    """
    Serializer for teacher card view (used in featured and listing pages)
    """
    subjects = TeacherSubjectSerializer(many=True, read_only=True)
    primary_subject = serializers.SerializerMethodField()
    total_students = serializers.IntegerField(read_only=True)
    total_courses = serializers.IntegerField(read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    total_reviews = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Teacher
        fields = [
            'id',
            'profile_image',
            'full_name',
            'title',
            'experience_years',
            'subjects',
            'primary_subject',
            'total_students',
            'total_courses',
            'average_rating',
            'total_reviews',
            'is_available'
        ]
    
    def get_primary_subject(self, obj):
        """Get primary subject display name"""
        primary = obj.subjects.filter(is_primary=True).first()
        if primary:
            return {
                'value': primary.subject,
                'label': primary.get_subject_display()
            }
        # If no primary, return first subject
        first_subject = obj.subjects.first()
        if first_subject:
            return {
                'value': first_subject.subject,
                'label': first_subject.get_subject_display()
            }
        return None


class TeacherDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for teacher detail view
    """
    subjects = TeacherSubjectSerializer(many=True, read_only=True)
    educations = TeacherEducationSerializer(many=True, read_only=True)
    achievements = TeacherAchievementSerializer(many=True, read_only=True)
    reviews = TeacherReviewSerializer(many=True, read_only=True)
    
    total_students = serializers.IntegerField(read_only=True)
    total_courses = serializers.IntegerField(read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    total_reviews = serializers.IntegerField(read_only=True)
    
    # Academy details
    academy_name = serializers.CharField(source='academy.name', read_only=True)
    academy_location = serializers.SerializerMethodField()
    academy_hours = serializers.CharField(source='academy.hours_text', read_only=True)
    
    class Meta:
        model = Teacher
        fields = [
            'id',
            'profile_image',
            'full_name',
            'title',
            'bio',
            'experience_years',
            'location',
            'linkedin_url',
            'email',
            'phone',
            'is_available',
            'subjects',
            'educations',
            'achievements',
            'reviews',
            'total_students',
            'total_courses',
            'average_rating',
            'total_reviews',
            'academy_name',
            'academy_location',
            'academy_hours'
        ]
    
    def get_academy_location(self, obj):
        """Get formatted academy location"""
        academy = obj.academy
        location_parts = []
        
        if academy.upazila:
            location_parts.append(academy.upazila.name)
        if academy.district:
            location_parts.append(academy.district.name)
        if academy.division:
            location_parts.append(academy.division.name)
        
        return ', '.join(location_parts) if location_parts else None


class SubjectFilterSerializer(serializers.Serializer):
    """
    Serializer for subject filter options
    """
    value = serializers.CharField()
    label = serializers.CharField()