from django.urls import path
from dashboard.apis.academy_dashboard import AcademyDashboardApi


academy_urlpatterns = [
    path('academy/', AcademyDashboardApi.as_view(), name='academy-dashboard'),
]

urlpatterns = [
    path('dashboard/', include(academy_urlpatterns)),
]