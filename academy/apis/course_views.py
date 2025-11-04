import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from functools import cached_property
from rest_framework_simplejwt.authentication import JWTAuthentication
from academy.selectors.course_selector import CourseSelector, CourseTypeSelector
from academy.services.course_service import CourseService
from academy.serializers import course_serializers
from classmate.permissions import AuthenticatedGenericView
logger = logging.getLogger(__name__)

class CourseCreateView(AuthenticatedGenericView, APIView):
    """
    API endpoint for creating courses with optional batch data.
    """
    serializer_class = course_serializers.CourseCreateSerializer
    
    @cached_property
    def course_service(self):
        """Lazy initialization of CourseService."""
        return CourseService(request_user=self.request.user)
    
    def post(self, request):
        """
        Create a course with optional batches.
        
        Request body:
        {
            "name": "Course Name",
            "description": "Course description",
            "fee": 1000.00,
            "academy_id": 1,
            "batches": [  // Optional
                {
                    "name": "Batch 1",
                    "start_date": "2023-01-01",
                    "end_date": "2023-06-30",
                    "description": "Batch description",
                    "is_active": true
                }
            ]
        }
        """
        try:
            # Validate request data
            serializer = self.serializer_class(data=request.data, context={'request': request})
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Extract data
            course_data = {
                'name': serializer.validated_data['name'],
                'description': serializer.validated_data['description'],
                'fee': serializer.validated_data['fee'],
                'academy_id': serializer.validated_data['academy_id']
            }
            
            batches_data = serializer.validated_data.get('batches', None)
            
            # Create course with optional batches
            course = self.course_service.create_course(
                data=course_data,
                batches_data=batches_data
            )
            
            # Return response
            response_serializer = course_serializers.CourseSerializer(course)
            return Response({
                'success': True,
                'message': 'Course created successfully',
                'data': response_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Log the exception
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Error in CourseCreateView: {str(e)}")
            
            return Response({
                'success': False,
                'error': 'An unexpected error occurred'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CourseUpdateView(AuthenticatedGenericView, APIView):
    """
    API endpoint for updating courses with optional batch data.
    """
    serializer_class = course_serializers.CourseCreateSerializer  # Reuse create serializer for updates

    @cached_property
    def course_service(self):
        """Lazy initialization of CourseService."""
        return CourseService(request_user=self.request.user)

    @cached_property
    def course_selector(self):
        """Lazy initialization of CourseSelector."""
        return CourseSelector()
    
    def put(self, request, course_id: int):
        """
        Update a course with optional batches.
        
        Request body:
        {
            "name": "Updated Course Name",
            "description": "Updated description",
            "fee": 1200.00,
            "academy_id": 1,
            "batches": [  // Optional
                {
                    "id": 1,  // Include ID for existing batches
                    "name": "Updated Batch 1",
                    "start_date": "2023-02-01",
                    "end_date": "2023-07-30"
                },
                {
                    "name": "New Batch",  // No ID means create new
                    "start_date": "2023-08-01",
                    "end_date": "2023-12-31"
                }
            ]
        }
        """
        try:
            # Check if course exists
            course = self.course_selector.get_course_by_id(course_id)
            if not course:
                return Response({
                    'success': False,
                    'error': 'Course not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Validate request data
            serializer = self.serializer_class(data=request.data, context={'request': request})
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Extract data
            course_data = {
                'name': serializer.validated_data['name'],
                'description': serializer.validated_data['description'],
                'fee': serializer.validated_data['fee'],
                'academy_id': serializer.validated_data['academy_id'],
                'course_type': serializer.validated_data['course_type']
            }

            batches_data = serializer.validated_data.get('batches', None)

            # Update course with optional batches
            updated_course = self.course_service.update_course(
                course_id=course_id,
                data=course_data,
                batches_data=batches_data
            )
            
            # Return response
            response_serializer = course_serializers.CourseSerializer(updated_course)
            return Response({
                'success': True,
                'message': 'Course updated successfully',
                'data': response_serializer.data
            }, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Log the exception
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Error in CourseUpdateView: {str(e)}")
            
            return Response({
                'success': False,
                'error': 'An unexpected error occurred'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CourseListView(AuthenticatedGenericView, APIView):
    """
    API endpoint for listing courses with batch details.
    """
    serializer_class = course_serializers.CourseSerializer

    @cached_property
    def course_selector(self):
        """Lazy initialization of CourseSelector."""
        return CourseSelector()
    
    def get(self, request):
        """
        List courses with batch details based on user role.
        
        Query parameters:
        - academy_id: Filter by academy ID
        - name: Filter by course name (partial match)
        - search: Search across name, description, and academy name
        - ordering: Order by field (e.g., name, fee, created_at)
        - page: Page number for pagination
        - page_size: Items per page
        """
        try:            
            search_query = request.query_params.get('search', '')
            ordering = request.query_params.get('ordering')
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            
            # Get courses using selector
            pagination_info = self.course_selector.list_courses(
                request=request,
                filters=request.GET,
                search_query=search_query,
                ordering=ordering,
                page=page,
                page_size=page_size
            )
            
            # Serialize data
            serializer = self.serializer_class(pagination_info['results'], many=True)
            
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
            # Log the exception
            import logging
            logger = logging.getLogger(__name__)
            logger.exception("Error in CourseListView")
            
            return Response(
                {
                    'success': False,
                    'error': 'Failed to retrieve courses',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
 
class CourseDropdownView(APIView):
    """
    API endpoint for course dropdown data with role-based filtering.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @cached_property
    def course_selector(self):
        """Lazy initialization of CourseSelector."""
        return CourseSelector()
    
    def get(self, request):
        """
        Get filtered students for dropdown selection.
        
        Query parameters:
        - academy_id: Optional filter by specific academy ID
        - search: Optional search term for student name or ID
        """
        try:
            # Extract query parameters
            academy_id = request.query_params.get('academy_id')
            search = request.query_params.get('search')
            
            # Validate numeric parameters
            if academy_id and not academy_id.isdigit():
                return Response(
                    {"detail": "Academy ID must be a valid integer."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Convert parameters to appropriate types
            academy_id = int(academy_id) if academy_id else None

            # Get courses using selector with role-based filtering
            courses = self.course_selector.get_courses_for_dropdown(
                request=request,
                academy_id=academy_id,
                search=search
            )

            # Serialize and return the data
            serializer = course_serializers.CourseDropdownSerializer(courses, many=True)
            return Response({
                'success': True,
                'data': serializer.data,
                'count': len(serializer.data)
            })
        
        except ValidationError as e:
            return Response(
                {
                    'success': False,
                    'error': 'Invalid parameters',
                    'details': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            # Log the exception
            import logging
            logger = logging.getLogger(__name__)
            logger.exception("Error in StudentDropdownView")
            
            return Response(
                {
                    'success': False,
                    'error': 'An unexpected error occurred',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CourseDeleteView(APIView):
    """
    API endpoint for deleting a course.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def delete(self, request, course_id):
        """
        Delete a course if it has no students enrolled in any of its batches.
        
        Args:
            course_id: ID of the course to delete
        
        Returns:
            Response with success message or error details
        """
        try:
            course_service = CourseService(request_user=request.user)
            result = course_service.delete_course(course_id)
            
            return Response(
                result,
                status=status.HTTP_200_OK
            )
            
        except ValidationError as e:
            return Response(
                {
                    'success': False,
                    'error': str(e),
                    'error_code': 'validation_error'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.exception(f"Error deleting course {course_id}: {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': 'An unexpected error occurred while deleting the course',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class CourseTypeDropdownView(APIView):
    """
    View to list all available course types.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    serializer_class = course_serializers.CourseTypeDropdownSerializer

    @cached_property
    def course_type_selector(self):
        """Lazy initialization of CourseTypeSelector."""
        return CourseTypeSelector()
    
    def get(self, request, format=None):
        """
        Get list of all available course types.
        
        Returns:
            Response with course types data
        """
        try:
            course_types = self.course_type_selector.list_course_types()
            serializer = self.serializer_class(course_types, many=True)
            
            return Response({
                'count': len(course_types),
                'results': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error in CourseTypeListView: {str(e)}")
            return Response(
                {"detail": "An error occurred while retrieving course types."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )