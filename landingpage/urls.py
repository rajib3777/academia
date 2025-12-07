from django.urls import path
from landingpage.apis.landing_page_apis import (
    FeaturedAcademiesAPIView,
    AcademyListingAPIView,
    AcademyDetailAPIView,
    ProgramFilterOptionsAPIView
)
from landingpage.apis.landing_page_teacher_api import (
    FeaturedTeachersAPIView,
    TeacherListingAPIView,
    TeacherDetailAPIView,
    SubjectFilterOptionsAPIView
)

academy_urlpatterns = [
    # Landing page URLs (public)
    path('landing/academies/featured/', FeaturedAcademiesAPIView.as_view(), name='landing-featured-academies'),
    path('landing/academies/', AcademyListingAPIView.as_view(), name='landing-academy-list'),
    path('landing/academies/<int:academy_id>/', AcademyDetailAPIView.as_view(), name='landing-academy-detail'),
    path('landing/academies/programs/', ProgramFilterOptionsAPIView.as_view(), name='landing-academy-program-filters'),
]

teacher_urlpatterns = [
    path('landing/teachers/featured/', FeaturedTeachersAPIView.as_view(), name='landing-featured-teachers'),
    path('landing/teachers/', TeacherListingAPIView.as_view(), name='landing-all-teachers'),
    path('landing/teachers/<int:id>/', TeacherDetailAPIView.as_view(), name='landing-teacher-detail'),
    path('landing/teachers/subjects/', SubjectFilterOptionsAPIView.as_view(), name='landing-subject-filters'),
]

urlpatterns = [
    *academy_urlpatterns,
    *teacher_urlpatterns,
]