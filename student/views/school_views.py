from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from student.selectors import school_selector
from student.services.school_service import SchoolService
from student.serializers.school_serializers import (
    SchoolCreateSerializer,
    SchoolUpdateSerializer,
    SchoolDetailSerializer,
    SchoolListSerializer,
)
from functools import cached_property
import logging

logger = logging.getLogger(__name__)


class SchoolCreateView(APIView):
    """
    API to create a new school.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    school_service = SchoolService()
    serializer_class = SchoolCreateSerializer

    def post(self, request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            school = self.school_service.create_school(serializer.validated_data)
            detail_serializer = SchoolDetailSerializer(school)
            return Response({'success': True, 'data': detail_serializer.data}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f'Error in SchoolCreateView: {str(e)}')
            return Response(
                {
                    'success': False,
                    'error': 'Failed to create school',
                    'details': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class SchoolUpdateView(APIView):
    """
    API to update an existing school.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    school_selector = school_selector.SchoolSelector()
    school_service = SchoolService()

    def put(self, request, school_id: int) -> Response:
        serializer = SchoolUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        school = self.school_selector.get_by_id(school_id)
        if not school:
            return Response({'detail': 'School not found.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            updated_school = self.school_service.update_school(school, serializer.validated_data)
            detail_serializer = SchoolDetailSerializer(updated_school)
            return Response({'success': True, 'data': detail_serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f'Error in SchoolUpdateView: {str(e)}')
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SchoolListView(APIView):
    """
    API to list all schools.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    serializer_class = SchoolListSerializer

    @cached_property
    def school_selector(self) -> school_selector.SchoolSelector:
        """Lazy initialization of SchoolSelector."""
        return school_selector.SchoolSelector()

    def get(self, request) -> Response:
        try:
            # Extract pagination parameters
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
            
            # Extract search and ordering parameters
            search_query = request.GET.get('search', '').strip()

            pagination_info = self.school_selector.list_schools(
                search_query=search_query,
                page=page,
                page_size=page_size
            )

            # Serialize data
            serializer = self.serializer_class(pagination_info['results'], context={'request': request}, many=True)

            # Build response
            response_data = {
                'success': True,
                'data': serializer.data,
                'pagination': pagination_info['pagination'],
                'filters_applied': dict(request.GET),
                'total_count': pagination_info['pagination']['total_items']
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f'Error in SchoolListView: {str(e)}')
            return Response(
                {
                    'success': False,
                    'error': 'Failed to retrieve schools',
                    'details': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class SchoolDeleteView(APIView):
    """
    API to delete a school.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    school_selector = school_selector.SchoolSelector()
    school_service = SchoolService()

    def delete(self, request, school_id: int) -> Response:
        school = self.school_selector.get_by_id(school_id)
        if not school:
            return Response({'detail': 'School not found.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            self.school_service.delete_school(school)
            return Response({'success': True}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f'Error in SchoolDeleteView: {str(e)}')
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)