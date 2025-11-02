from django.urls import path
from payment.apis import student_payment_apis

urlpatterns = [
    path('student/payments/', student_payment_apis.StudentPaymentListView.as_view(), name='student-payment-list'),
    path('student/payments/create/', student_payment_apis.StudentPaymentCreateView.as_view(), name='student-payment-create'),
    path('student/payments/<int:payment_id>/', student_payment_apis.StudentPaymentDetailView.as_view(), name='student-payment-detail'),
    path('student/payments/<int:payment_id>/update/', student_payment_apis.StudentPaymentUpdateView.as_view(), name='student-payment-update'),
    path('student/payments/<int:payment_id>/delete/', student_payment_apis.StudentPaymentDeleteView.as_view(), name='student-payment-delete'),
]
