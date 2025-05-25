from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SchoolViewSet

school_router = DefaultRouter()
school_router.register(r'schools', SchoolViewSet, basename='school')

urlpatterns = [
    path('', include(school_router.urls)),
]
