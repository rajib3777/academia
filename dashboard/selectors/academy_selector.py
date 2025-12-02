from django.db.models import Sum, Count
from academy.models import Academy, Course, Batch, BatchEnrollment
from payment.models import StudentPayment
from student.models import Student

class AcademyDashboardSelector:
    def __init__(self, user):
        self.user = user
    
    @staticmethod
    def get_academy_id_for_user(user: User) -> int | None:
        if not user.is_academy():
            return None
        return user.academy.first() if hasattr(user, "academy") else None

    @staticmethod
    def get_dashboard_data_for_academy(user: User) -> Dict[str, Any]:
        academy = AcademyDashboardSelector.get_academy_id_for_user(user)
        if not academy:
            return None

        course_qs = Course.objects.filter(academy=academy)
        batch_qs = Batch.objects.filter(course__academy=academy)

        # Basic Counts
        total_courses = course_qs.count()
        total_batches = batch_qs.count()
        active_batches = batch_qs.filter(is_active=True).count()
        
        # Total Students (Unique students enrolled in any batch of this academy)

        # total_students = Student.objects.filter(
        #     enrolled_batches__course__academy=academy
        # ).distinct().count()

        enrollment_qs = BatchEnrollment.objects.filter(
            batch__course__academy_id=academy_id,
            is_active=True,
        )
        total_students = (
            enrollment_qs.values("student_id").distinct().count()
        )

        # Total Revenue
        # total_revenue = StudentPayment.objects.filter(
        #     batch_enrollment__batch__course__academy=academy
        # ).aggregate(total=Sum('amount'))['total'] or 0

        # Payments for this academy
        payments_qs = StudentPayment.objects.filter(
            batch_enrollment__batch__course__academy_id=academy_id
        )

        total_revenue = (
            payments_qs.aggregate(total=Sum("amount"))["total"] or 0
        )

        # Monthly revenue for last 6 months
        now = timezone.now()
        start_period = (now.replace(day=1) - timedelta(days=5 * 30)).replace(day=1)

        monthly = (
            payments_qs.filter(date__gte=start_period)
            .annotate(month=timezone.datetime(
                year=timezone.F("date__year"),
                month=timezone.F("date__month"),
                day=1,
                tzinfo=timezone.utc,
            ))
        )
        # Simpler: group using date__year / date__month with values
        monthly = (
            payments_qs.filter(date__gte=start_period)
            .values("date__year", "date__month")
            .annotate(total=Sum("amount"))
            .order_by("date__year", "date__month")
        )

        monthly_revenue: List[Dict[str, Any]] = [
            {
                "year": row["date__year"],
                "month": row["date__month"],
                "total": row["total"] or 0,
            }
            for row in monthly
        ]

        # Recent Enrollments (limit 5)
        recent_enrollments = BatchEnrollment.objects.filter(
            batch__course__academy=academy
        ).select_related('student__user', 'batch__course').order_by('-enrollment_date')[:5]

        # Recent Payments (limit 5)
        recent_payments = StudentPayment.objects.filter(
            batch_enrollment__batch__course__academy=academy
        ).select_related('student__user', 'batch_enrollment__batch').order_by('-date')[:5]

        return {
            "academy_name": academy.name,
            "total_students": total_students,
            "total_courses": total_courses,
            "total_batches": total_batches,
            "active_batches": active_batches,
            "total_revenue": total_revenue,
            "monthly_revenue": monthly_revenue,
            "recent_enrollments": recent_enrollments,
            "recent_payments": recent_payments
        }
