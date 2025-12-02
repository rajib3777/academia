from rest_framework import serializers
from academy.models import BatchEnrollment
from payment.models import StudentPayment

class DashboardRecentEnrollmentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    course_name = serializers.CharField(source='batch.course.name', read_only=True)
    batch_name = serializers.CharField(source='batch.name', read_only=True)

    class Meta:
        model = BatchEnrollment
        fields = ['id', 'student_name', 'course_name', 'batch_name', 'enrollment_date']

class DashboardRecentPaymentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    batch_name = serializers.CharField(source='batch_enrollment.batch.name', read_only=True)
    
    class Meta:
        model = StudentPayment
        fields = ['id', 'student_name', 'batch_name', 'amount', 'date', 'status', 'transaction_id']


class AcademyDashboardMonthlyRevenueSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    month = serializers.IntegerField()
    total = serializers.DecimalField(max_digits=12, decimal_places=2)


class AcademyDashboardSerializer(serializers.Serializer):
    academy_name = serializers.CharField()
    total_students = serializers.IntegerField()
    total_courses = serializers.IntegerField()
    total_batches = serializers.IntegerField()
    active_batches = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    monthly_revenue = AcademyDashboardMonthlyRevenueSerializer(many=True)
    recent_enrollments = DashboardRecentEnrollmentSerializer(many=True)
    recent_payments = DashboardRecentPaymentSerializer(many=True)
