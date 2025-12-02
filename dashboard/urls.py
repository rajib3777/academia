from django.urls import path, include
from dashboard.apis.academy_dashboard_api import AcademyDashboardApi


academy_urlpatterns = [
    path('academy/', AcademyDashboardApi.as_view(), name='academy-dashboard'),
]

urlpatterns = [
    path('dashboard/', include(academy_urlpatterns)),
]