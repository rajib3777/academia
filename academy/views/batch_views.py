from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from functools import cached_property
from rest_framework_simplejwt.authentication import JWTAuthentication
from classmate.permissions import AuthenticatedGenericView
from academy.selectors.batch_selector import BatchSelector
from academy.services.batch_service import BatchService
from academy.serializers.batch_serializers import BatchSerializer

class BatchCreateView(APIView):
    """
    API endpoint for creating batches.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    @cached_property
    def batch_service(self):
        """Lazy initialization of BatchService."""
        return BatchService(user=self.request.user)
    
    def post(self, request):
        """
        Create a new batch.
        
        Request body:
        {
            "name": "Batch Name",
            "course_id": 1,
            "start_date": "2023-01-01",
            "end_date": "2023-06-30",
            "description": "Batch description",
            "is_active": true
        }
        """
        try:
            # Validate request data
            serializer = BatchSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create batch
            batch = self.batch_service.create_batch(serializer.validated_data)
            
            # Return response
            response_serializer = BatchSerializer(batch)
            return Response({
                'success': True,
                'message': 'Batch created successfully',
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
            logger.exception(f"Error in BatchCreateView: {str(e)}")
            
            return Response({
                'success': False,
                'error': 'An unexpected error occurred'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BatchUpdateView(APIView):
    """
    API endpoint for updating batches.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    @cached_property
    def batch_service(self):
        """Lazy initialization of BatchService."""
        return BatchService(user=self.request.user)
    
    @cached_property
    def batch_selector(self):
        """Lazy initialization of BatchSelector."""
        return BatchSelector()
    
    def put(self, request, batch_id):
        """
        Update an existing batch.
        
        Request body:
        {
            "name": "Updated Batch Name",
            "course_id": 1,
            "start_date": "2023-02-01",
            "end_date": "2023-07-30",
            "description": "Updated description",
            "is_active": true
        }
        """
        try:
            # Check if batch exists
            batch = self.batch_selector.get_batch_by_id(batch_id)
            if not batch:
                return Response({
                    'success': False,
                    'error': 'Batch not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Validate request data
            serializer = BatchSerializer(data=request.data, partial=True)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update batch
            updated_batch = self.batch_service.update_batch(
                batch_id=batch_id,
                data=serializer.validated_data
            )
            
            # Return response
            response_serializer = BatchSerializer(updated_batch)
            return Response({
                'success': True,
                'message': 'Batch updated successfully',
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
            logger.exception(f"Error in BatchUpdateView: {str(e)}")
            
            return Response({
                'success': False,
                'error': 'An unexpected error occurred'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BatchListView(AuthenticatedGenericView, APIView):
    """
    API endpoint for listing batches with advanced filtering.
    """
    serializer_class = BatchSerializer
    
    @cached_property
    def batch_selector(self):
        """Lazy initialization of BatchSelector."""
        return BatchSelector()
    
    def get(self, request):
        """
        List batches with advanced filtering options.
        
        Query parameters:
        - academy_id: Filter by academy ID
        - course_id: Filter by course ID
        - name: Filter by batch name (partial match)
        - is_active: Filter by active status (true/false)
        - start_date_from: Filter batches starting after this date
        - start_date_to: Filter batches starting before this date
        - end_date_from: Filter batches ending after this date
        - end_date_to: Filter batches ending before this date
        - has_students: Filter batches with/without students (true/false)
        - search: Search across name, description, course name, and academy name
        - ordering: Order by field (e.g., name, start_date, end_date, course__name)
        - page: Page number for pagination
        - page_size: Items per page
        """
        try:
            search_query = request.query_params.get('search', '')
            ordering = request.query_params.get('ordering')
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            
            # Get batches using selector
            pagination_info = self.batch_selector.list_batches(
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
            logger.exception("Error in BatchListView")

            return Response(
                {
                    'success': False,
                    'error': 'Failed to retrieve batches',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )