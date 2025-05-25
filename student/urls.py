from django.urls import path, include
from rest_framework.routers import DefaultRouter
from student.views import SchoolViewSet, SchoolNameListAPIView

school_router = DefaultRouter()
school_router.register(r'schools', SchoolViewSet, basename='school')

school_urlpatterns = [
    path('', include(school_router.urls)),
]

# Public (with auth) routes
public_urlpatterns = [
    path('school-name-list/', SchoolNameListAPIView.as_view(), name='public-school-name-list'),
]

urlpatterns = school_urlpatterns + public_urlpatterns
