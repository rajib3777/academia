from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser
import logging
from functools import cached_property
from academy.serializers.academy_serializers_v2 import (
    AcademyCreateUpdateSerializer,
    AcademyListSerializer
)
from academy.selectors import academy_selector_v2
from academy.services import academy_service_v2
from account.selectors import user_selector
from account.services import user_service
from academy.serializers import academy_serializers_v2
from django.core.exceptions import ValidationError

# Configure logger
logger = logging.getLogger(__name__)


class AcademyListView(APIView):
    """List academies with pagination and filtering."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    serializer_class = AcademyListSerializer
    
    @cached_property
    def academy_selector(self) -> academy_selector_v2.AcademySelector:
        """Lazy initialization of AcademySelector."""
        return academy_selector_v2.AcademySelector()
        
    def get(self, request):
        """
        Get list of academies with advanced filtering, pagination, and optimization.
        
        Returns:
            Response with paginated academies data
        """
        try:
            # Extract pagination parameters
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
            
            # Extract search and ordering parameters
            search_query = request.GET.get('search', '').strip()
            ordering = request.GET.get('ordering')
            academy_id = request.GET.get('academy_id')
            
            # Whitelist allowed filter parameters
            # allowed_filters = {'division', 'district', 'upazila', 'is_active', 'established_year'}
            # filters = {k: v for k, v in request.query_params.items() if k in allowed_filters}
            
            # Get academies with selector
            pagination_info = self.academy_selector.list_academies(
                request_user=request.user,
                academy_id=academy_id,
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
            logger.error(f"Error in AcademyListView: {str(e)}")
            
            return Response(
                {
                    'success': False,
                    'error': 'An error occurred while retrieving academies.',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AcademyCreateView(APIView):
    """Create a new academy."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service_class = academy_service_v2.AcademyService()
        self.selector_class = academy_selector_v2.AcademySelector()

    def post(self, request, format=None):
        """
        Create a new academy with user data.
        
        Returns:
            Response with created academy data or error details
        """
        serializer = academy_serializers_v2.AcademyCreateUpdateSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            try:
                serializer.is_valid(raise_exception=True)
                academy = self.service_class.create_academy(serializer.validated_data)
                
                # Get the created academy with all related data for response
                detailed_academy = self.selector_class.get_academy_by_id(academy.id)
                response_serializer = academy_serializers_v2.AcademyListSerializer(detailed_academy)

                return Response({'success': True, 'data': response_serializer.data}, status=status.HTTP_201_CREATED)
            
            except ValidationError as e:
                logger.error(f"Validation error in AcademyCreateView: {str(e)}")
                return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
            except Exception as e:
                logger.error(f"Error in AcademyCreateView: {str(e)}")
                return Response({'detail': 'An error occurred while creating the academy.'}, 
                               status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AcademyDetailView(APIView):
    """Get academy details by ID."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selector_class = academy_selector_v2.AcademySelector()

    def get(self, request, academy_id=None, format=None):
        """
        Get detailed information about an academy.
        
        Args:
            academy_id: ID of the academy to retrieve
            
        Returns:
            Response with academy details or error
        """
        try:
            # Check if user is allowed to view this academy
            if not request.user.is_superuser and not request.user.is_admin() and not request.user.is_academy():
                return Response({'detail': 'You do not have permission to view this academy'}, 
                                status=status.HTTP_403_FORBIDDEN)
            
            if request.user.is_academy():
                academy = self.selector_class.get_academy_details_by_user(request.user)
            elif request.user.is_superuser or request.user.is_admin():
                if not academy_id:
                    return Response({'detail': 'Academy ID is required'}, status=status.HTTP_400_BAD_REQUEST)
                academy = self.selector_class.get_academy_details_by_id(academy_id)
            else:
                return Response({'detail': 'You do not have permission to view this academy'}, status=status.HTTP_403_FORBIDDEN)
            
            if not academy:
                return Response({'detail': 'Academy not found'}, status=status.HTTP_404_NOT_FOUND)
                    
            serializer = AcademyListSerializer(academy)
            return Response(serializer.data)
        
        except Exception as e:
            logger.error(f"Error in AcademyDetailView: {str(e)}")
            return Response({'detail': 'An error occurred while retrieving the academy details.'}, 
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AcademyAccountDetailView(APIView):
    """Get academy account details by ID."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selector_class = academy_selector_v2.AcademySelector()

    def get(self, request, format=None):
        """
        Get detailed information about an academy.
        
        Args:
            academy_id: ID of the academy to retrieve
            
        Returns:
            Response with academy details or error
        """
        try:
            request_user = request.user
            if not request_user.is_academy():
                return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
            
            academy = self.selector_class.get_by_user(request_user)
            if not academy:
                return Response({'detail': 'Academy not found.'}, status=status.HTTP_404_NOT_FOUND)

            serializer = academy_serializers_v2.AcademyAccountDetailSerializer(academy, context={'request': request})
            return Response({'success': True, 'data': serializer.data}, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f'Error in AcademyAccountDetailView: {str(e)}')
            return Response({'success': False, 'error': 'An error occurred while retrieving academy details.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AcademyUpdateView(APIView):
    """Update an existing academy."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service_class = academy_service_v2.AcademyService()
        self.selector_class = academy_selector_v2.AcademySelector()

    def put(self, request, academy_id, format=None):
        """
        Update an academy and its associated user.
        
        Args:
            academy_id: ID of the academy to update
            
        Returns:
            Response with updated academy data or error details
        """
        try:
            # Get the academy first to check permissions
            academy = self.selector_class.get_academy_by_id(academy_id)
            
            if not academy:
                return Response({'detail': 'Academy not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Check if user is allowed to update this academy
            if not request.user.is_superuser and not request.user.is_admin() and not request.user.is_academy():
                return Response({'detail': 'You do not have permission to update this academy'}, 
                               status=status.HTTP_403_FORBIDDEN)
            
            # Update the academy
            serializer = AcademyCreateUpdateSerializer(data=request.data, partial=True)
            
            if serializer.is_valid():
                try:
                    updated_academy = self.service_class.update_academy(academy_id, serializer.validated_data)
                    
                    if updated_academy:
                        # Get the updated academy with all related data for response
                        detailed_academy = self.selector_class.get_academy_by_id(academy_id)
                        response_serializer = AcademyListSerializer(detailed_academy)
                        return Response(response_serializer.data)
                    
                    return Response({'detail': 'Failed to update academy'}, 
                                   status=status.HTTP_400_BAD_REQUEST)
                
                except ValidationError as e:
                    return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Error in AcademyUpdateView: {str(e)}")
            return Response({'detail': 'An error occurred while updating the academy.'}, 
                           status=status.HTTP_400_BAD_REQUEST)


class AcademyDeleteView(APIView):
    """Delete an academy and its related data."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service_class = academy_service_v2.AcademyService()

    def delete(self, request, academy_id, format=None):
        """
        Delete an academy and all related courses, batches, and enrollments.
        Does not delete any Student records.
        
        Args:
            academy_id: ID of the academy to delete
            
        Returns:
            Response indicating success or failure
        """
        try:
            success = self.service_class.delete_academy(academy_id)
            
            if success:
                return Response(status=status.HTTP_204_NO_CONTENT)
            
            return Response({'detail': 'Academy not found'}, 
                           status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.error(f"Error in AcademyDeleteView: {str(e)}")
            return Response({'detail': 'An error occurred while deleting the academy.'}, 
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AcademyAccountUpdateView(APIView):
    """
    API for academy users to update their own account and academy profile.
    Allows password change.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    academy_selector = academy_selector_v2.AcademySelector()
    academy_service = academy_service_v2.AcademyService()
    user_service = user_service.UserService()

    def put(self, request):
        request_user = request.user
        if not request_user.is_academy():
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        academy = self.academy_selector.get_by_user(request_user)
        serializer = academy_serializers_v2.AcademyAccountUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # Update user fields
            user_update_data = serializer.validated_data.get('user', {})
            if user_update_data:
                self.user_service.update_user(request_user.id, user_update_data)

            # Update academy fields
            academy_update_data = serializer.validated_data.get('academy', {})
            if academy_update_data:
                self.academy_service.update_academy_account(academy, academy_update_data)

            return Response({'detail': 'Account updated successfully.'}, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
