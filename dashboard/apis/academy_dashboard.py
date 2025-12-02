from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from academy.selectors.dashboard_selector import AcademyDashboardSelector
from academy.serializers.dashboard_serializers import AcademyDashboardSerializer

class AcademyDashboardApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        selector = AcademyDashboardSelector(user=request.user)
        data = selector.get_dashboard_data()

        if data is None:
            return Response(
                {"detail": "Academy not found for this user."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AcademyDashboardSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
