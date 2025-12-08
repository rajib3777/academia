from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
import logging
from landingpage.selectors.landing_page_selector import LandingPageAcademySelector
from landingpage.serializers.landing_page_serializers import (
    FeaturedAcademySerializer,
    AcademyDetailSerializer,
    ProgramFilterSerializer,
    ContactUsSerializer
)
logger = logging.getLogger(__name__)

class FeaturedAcademiesAPIView(APIView):
    """
    Public API to get featured academies for the main landing page.
    No authentication required.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        Get featured academies.
        
        Query Parameters:
            limit (optional): Number of academies to return (default: 6)
        
        Returns:
            Response with featured academies data
        """
        try:
            limit = int(request.GET.get('limit', 6))
            limit = min(limit, 12)  # Max 12 academies
            
            # Get featured academies using selector
            academies = LandingPageAcademySelector.get_featured_academies(limit=limit)
            
            # Serialize data
            serializer = FeaturedAcademySerializer(academies, many=True)
            
            return Response({
                'success': True,
                'data': serializer.data,
                'total_count': len(serializer.data)
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error in FeaturedAcademiesAPIView: {str(e)}")
            return Response({
                'success': False,
                'error': 'An error occurred while fetching featured academies.',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AcademyListingAPIView(APIView):
    """
    Public API to get all academies with filtering and pagination.
    No authentication required.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        Get all academies with filters.
        
        Query Parameters:
            search (optional): Search term for academy name/description
            program (optional): Filter by program name
            division (optional): Filter by division ID
            district (optional): Filter by district ID
            min_rating (optional): Minimum rating filter (0.0 - 5.0)
            page (optional): Page number (default: 1)
            page_size (optional): Items per page (default: 12, max: 24)
        
        Returns:
            Response with paginated academies data
        """
        try:
            # Extract query parameters
            search_query = request.GET.get('search', '').strip()
            program_filter = request.GET.get('program', '').strip()
            division_id = request.GET.get('division')
            district_id = request.GET.get('district')
            min_rating = request.GET.get('min_rating')
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 24))
            
            # Validate and limit page_size
            page_size = min(page_size, 24)
            
            # Convert to appropriate types
            if division_id:
                division_id = int(division_id)
            if district_id:
                district_id = int(district_id)
            if min_rating:
                min_rating = float(min_rating)
            
            # Get academies using selector
            result = LandingPageAcademySelector.get_all_academies_for_listing(
                search_query=search_query if search_query else None,
                program_filter=program_filter if program_filter else None,
                division_id=division_id,
                district_id=district_id,
                min_rating=min_rating,
                page=page,
                page_size=page_size
            )
            
            # Serialize data
            serializer = FeaturedAcademySerializer(result['results'], many=True)
            
            return Response({
                'success': True,
                'data': serializer.data,
                'pagination': result['pagination'],
                'filters_applied': {
                    'search': search_query if search_query else None,
                    'program': program_filter if program_filter else None,
                    'division': division_id,
                    'district': district_id,
                    'min_rating': min_rating
                }
            }, status=status.HTTP_200_OK)
        
        except ValueError as e:
            return Response({
                'success': False,
                'error': 'Invalid parameter value.',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Error in AcademyListingAPIView: {str(e)}")
            return Response({
                'success': False,
                'error': 'An error occurred while fetching academies.',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AcademyDetailAPIView(APIView):
    """
    Public API to get detailed academy information.
    No authentication required.
    """
    permission_classes = [AllowAny]
    
    def get(self, request, academy_id):
        """
        Get detailed academy information.
        
        Args:
            academy_id: ID of the academy
        
        Returns:
            Response with detailed academy data
        """
        try:
            # Get academy details using selector
            academy = LandingPageAcademySelector.get_academy_details_for_landing(academy_id)
            
            if not academy:
                return Response({
                    'success': False,
                    'error': 'Academy not found.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Serialize data
            serializer = AcademyDetailSerializer(academy)
            
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error in AcademyDetailAPIView: {str(e)}")
            return Response({
                'success': False,
                'error': 'An error occurred while fetching academy details.',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProgramFilterOptionsAPIView(APIView):
    """
    Public API to get available program filter options.
    No authentication required.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        Get list of available programs for filtering.
        
        Returns:
            Response with program options
        """
        try:
            # Get programs using selector
            programs = LandingPageAcademySelector.get_available_programs()
            
            # Format as list of objects
            program_data = [{'name': program} for program in programs]
            
            # Serialize data
            serializer = ProgramFilterSerializer(program_data, many=True)
            
            return Response({
                'success': True,
                'data': serializer.data,
                'total_count': len(serializer.data)
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error in ProgramFilterOptionsAPIView: {str(e)}")
            return Response({
                'success': False,
                'error': 'An error occurred while fetching program options.',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ContactUsAPIView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            serializer = ContactUsSerializer(data=request.data)
            
            if serializer.is_valid():
                contact_us = serializer.save()

                return Response({
                    'success': True,
                    'message': 'Thank you for contacting us! We will get back to you soon.',
                }, status=status.HTTP_201_CREATED)
            
            logger.warning(f"Contact us form validation failed: {serializer.errors}")
            return Response({
                'success': False,
                'message': 'Validation failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error submitting contact us form: {str(e)}")
            return Response({
                'success': False,
                'message': 'An error occurred while submitting the form. Please try again later.',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)