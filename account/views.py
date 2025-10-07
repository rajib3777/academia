from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.exceptions import ValidationError
from account.serializers import ChangePasswordSerializer
from account.services.user_service import UserService
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