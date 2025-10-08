from django.urls import path, include
from rest_framework.routers import DefaultRouter
from student.views.student_views import (SchoolNameListAPIView, StudentListCreateAPIView, StudentRetrieveUpdateDestroyAPIView, 
                           StudentCreateView, StudentUpdateView, StudentListV1View, StudentActivateView, StudentDropdownView, 
                           StudentAccountUpdateView, StudentAccountDetailView, SchoolDropdownView)
from student.views.school_views import SchoolListView, SchoolCreateView, SchoolUpdateView, SchoolDeleteView

school_urlpatterns = [
    path('v1/schools/', SchoolListView.as_view(), name='school-list'),
    path('v1/schools/create/', SchoolCreateView.as_view(), name='school-create'),
    path('v1/schools/<int:school_id>/update/', SchoolUpdateView.as_view(), name='school-update'),
    path('v1/schools/<int:school_id>/delete/', SchoolDeleteView.as_view(), name='school-delete'),

]

dropdown_urlpatterns = [
    path('students/dropdown/', StudentDropdownView.as_view(), name='student-dropdown'),
    path('schools/dropdown/', SchoolDropdownView.as_view(), name='school-dropdown'),
]

student_urlpatterns = [
    path('students/', StudentListCreateAPIView.as_view(), name='student-list-create'),
    path('v1/student/account/update/', StudentAccountUpdateView.as_view(), name='student-account-update'), # not in use. use /account/update/ from account app
    path('v1/student/account/details/', StudentAccountDetailView.as_view(), name='student-account-details'), # not in use. use /account/details/ from account app
    path('v1/students/create/', StudentCreateView.as_view(), name='student_create'),
    path('v1/students/<str:student_id>/update/', StudentUpdateView.as_view(), name='student_update'),
    path('v1/students/', StudentListV1View.as_view(), name='student_list'),
    path('v1/students/<int:student_id>/', StudentRetrieveUpdateDestroyAPIView.as_view(), name='student_detail'),
    path('v1/students/<int:student_id>/activate/', StudentActivateView.as_view(), name='student-activate'),
    # path('student/<int:pk>/', StudentRetrieveUpdateDestroyAPIView.as_view(), name='student-detail'),
]

# Public (with auth) routes
public_urlpatterns = [
    path('school-name-list/', SchoolNameListAPIView.as_view(), name='public-school-name-list'),
]

urlpatterns = school_urlpatterns + student_urlpatterns + public_urlpatterns + dropdown_urlpatterns
