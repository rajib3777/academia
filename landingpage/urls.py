from django.urls import path
from landingpage.apis.landing_page_apis import (
    FeaturedAcademiesAPIView,
    AcademyListingAPIView,
    AcademyDetailAPIView,
    ProgramFilterOptionsAPIView
)
urlpatterns = [
    # Landing page URLs (public)
    path('landing/featured/', FeaturedAcademiesAPIView.as_view(), name='landing-featured-academies'),
    path('landing/academies/', AcademyListingAPIView.as_view(), name='landing-academy-list'),
    path('landing/academies/<int:academy_id>/', AcademyDetailAPIView.as_view(), name='landing-academy-detail'),
    path('landing/programs/', ProgramFilterOptionsAPIView.as_view(), name='landing-program-filters'),
]