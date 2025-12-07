from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from landingpage.selectors.landing_page_teacher_selector import LandingPageTeacherSelector
from landingpage.serializers.landing_page_teacher_serializer import (
    TeacherCardSerializer,
    TeacherDetailSerializer,
    SubjectFilterSerializer
)


class FeaturedTeachersAPIView(APIView):
    """
    GET /api/teacher/landing/featured/
    Get featured teachers for main landing page
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get featured teachers"""
        limit = int(request.GET.get('limit', 6))
        limit = min(limit, 12)  # Max 12 teachers
        
        teachers = LandingPageTeacherSelector.get_featured_teachers(limit=limit)
        serializer = TeacherCardSerializer(teachers, many=True)
        
        return Response({
            'success': True,
            'count': len(serializer.data),
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class TeacherListingAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get all teachers with filters"""
        # Extract query parameters
        search = request.query_params.get('search', None)
        subject = request.query_params.get('subject', None)
        min_experience = request.query_params.get('min_experience', None)
        max_experience = request.query_params.get('max_experience', None)
        min_rating = request.query_params.get('min_rating', None)
        is_available = request.query_params.get('is_available', None)

        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 24))
        
        # Validate and limit page_size
        page_size = min(page_size, 24)
        
        # Get filtered teachers
        result = LandingPageTeacherSelector.get_all_teachers_with_filters(
            search=search,
            subject=subject,
            min_experience=min_experience,
            max_experience=max_experience,
            min_rating=min_rating,
            is_available=is_available,
            page=page,
            page_size=page_size
        )
        
        serializer = TeacherCardSerializer(result['results'], many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'pagination': result['pagination'],
            'filters': {
                'search': search,
                'subject': subject,
                'min_experience': min_experience,
                'max_experience': max_experience,
                'min_rating': min_rating,
                'is_available': is_available
            },
        }, status=status.HTTP_200_OK)
        
        # Convert to appropriate types
        try:
            if min_experience:
                min_experience = int(min_experience)
            if max_experience:
                max_experience = int(max_experience)
            if min_rating:
                min_rating = float(min_rating)
            if is_available:
                is_available = is_available.lower() == 'true'
        except (ValueError, TypeError):
            return Response({
                'success': False,
                'message': 'Invalid filter parameters'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get filtered teachers
        teachers = LandingPageTeacherSelector.get_all_teachers_with_filters(
            search=search,
            subject=subject,
            min_experience=min_experience,
            max_experience=max_experience,
            min_rating=min_rating,
            is_available=is_available
        )
        
        serializer = TeacherCardSerializer(teachers, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'count': len(serializer.data),
            'filters': {
                'search': search,
                'subject': subject,
                'min_experience': min_experience,
                'max_experience': max_experience,
                'min_rating': min_rating,
                'is_available': is_available
            },
        }, status=status.HTTP_200_OK)


class TeacherDetailAPIView(APIView):
    """
    GET /api/teacher/landing/teachers/{id}/
    Get teacher details by ID
    """
    permission_classes = [AllowAny]
    
    def get(self, request, id):
        """Get teacher details"""
        teacher = LandingPageTeacherSelector.get_teacher_by_id(id)
        
        if not teacher:
            return Response({
                'success': False,
                'message': 'Teacher not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = TeacherDetailSerializer(teacher)
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class SubjectFilterOptionsAPIView(APIView):
    """
    GET /api/teacher/landing/subjects/
    Get subject filter options
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get subject filter options"""
        subjects = LandingPageTeacherSelector.get_subject_filter_options()
        serializer = SubjectFilterSerializer(subjects, many=True)
        
        return Response({
            'success': True,
            'count': len(serializer.data),
            'data': serializer.data
        }, status=status.HTTP_200_OK)