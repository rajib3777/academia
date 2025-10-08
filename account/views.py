from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.exceptions import ValidationError
from account.serializers import ChangePasswordSerializer
from account.services.user_service import UserService
from academy.selectors import academy_selector_v2
from student.selectors import student_selector
from academy.serializers import academy_serializers_v2
from student.serializers import student_serializers
from academy.services import academy_service_v2
from student.services import student_service
from account.services import user_service

import logging

logger = logging.getLogger(__name__)

class ChangePasswordView(APIView):
    """
    API endpoint for authenticated users to change their password.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    user_service = UserService()

    def post(self, request) -> Response:
        """
        Change the password for the authenticated user.

        Returns:
            Response with success or error message.
        """
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        request_user = request.user
        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']
        confirm_password = serializer.validated_data['confirm_password']

        if not request_user.check_password(old_password):
            return Response(
                {'detail': 'Old password is incorrect.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_password != confirm_password:
            return Response(
                {'detail': 'New password and confirm password do not match.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            self.user_service.set_password(request_user, new_password)
            return Response({'detail': 'Password changed successfully.'}, status=status.HTTP_200_OK)
        except ValidationError as e:
            logger.error(f'Password change error: {str(e)}')
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f'Unexpected error in ChangePasswordView: {str(e)}')
            return Response({'detail': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class AccountDetailView(APIView):
    """Get academy account details by ID."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.academy_selector_class = academy_selector_v2.AcademySelector()
        self.student_selector_class = student_selector.StudentSelector()

    def get(self, request, format=None):
        try:
            request_user = request.user

            if hasattr(request_user, 'role') and request_user.is_academy():
                academy = self.academy_selector_class.get_by_user(request_user)

                if not academy:
                    return Response({'detail': 'Academy not found.'}, status=status.HTTP_404_NOT_FOUND)

                serializer = academy_serializers_v2.AcademyAccountDetailSerializer(academy, context={'request': request})
            elif hasattr(request_user, 'role') and request_user.is_student():
                student = self.student_selector_class.get_student_by_user(request_user)

                if not student:
                    return Response({'detail': 'Student not found.'}, status=status.HTTP_404_NOT_FOUND)

                serializer = student_serializers.StudentAccountDetailSerializer(student, context={'request': request})
            else:
                return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
            
            return Response({'success': True, 'data': serializer.data}, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f'Error in AccountDetailView: {str(e)}')
            return Response({'success': False, 'error': 'An error occurred while retrieving account details.'},
                            status=status.HTTP_400_BAD_REQUEST)
        

class AccountUpdateView(APIView):
    """
    API for academy users to update their own account and academy profile.
    Allows password change.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    academy_selector = academy_selector_v2.AcademySelector()
    academy_service = academy_service_v2.AcademyService()
    student_selector = student_selector.StudentSelector()
    student_service = student_service.StudentService()
    user_service = user_service.UserService()

    def put(self, request):
        request_user = request.user

        if hasattr(request_user, 'role') and request_user.is_academy():
            academy = self.academy_selector.get_by_user(request_user)
            serializer = academy_serializers_v2.AcademyAccountUpdateSerializer(data=request.data)

            try:
                serializer.is_valid(raise_exception=True)
            except DRFValidationError as e:
                logger.error(f'Serializer validation error: {e.detail}')
                return Response(
                    {'detail': 'Validation error', 'errors': e.detail},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user_update_data = serializer.validated_data.get('user', {})
            academy_update_data = serializer.validated_data.get('academy', {})

            if not user_update_data and not academy_update_data:
                return Response(
                    {'detail': 'No data provided for update.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                if user_update_data:
                    self.user_service.update_user(request_user.id, user_update_data)

                if academy_update_data:
                    self.academy_service.update_academy_account(academy, academy_update_data)

                return Response({'detail': 'Academy updated successfully.'}, status=status.HTTP_200_OK)
            except ValidationError as e:
                return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f'Unexpected error in AccountUpdateView: {str(e)}')
                return Response({'detail': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        elif hasattr(request_user, 'role') and request_user.is_student():
            student = self.student_selector.get_student_by_user(request_user)
            serializer = student_serializers.StudentAccountUpdateSerializer(data=request.data)

            try:
                serializer.is_valid(raise_exception=True)
            except DRFValidationError as e:
                logger.error(f'Serializer validation error: {e.detail}')
                return Response(
                    {'detail': 'Validation error', 'errors': e.detail},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user_update_data = serializer.validated_data.get('user', {})
            student_update_data = serializer.validated_data.get('student', {})

            if not user_update_data and not student_update_data:
                return Response(
                    {'detail': 'No data provided for update.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                if user_update_data:
                    self.user_service.update_user(request_user.id, user_update_data)

                if student_update_data:
                    self.student_service.update_student_account(student, student_update_data)

                return Response({'detail': 'Student updated successfully.'}, status=status.HTTP_200_OK)
            except ValidationError as e:
                return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f'Unexpected error in AccountUpdateView: {str(e)}')
                return Response({'detail': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        
