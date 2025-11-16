from django.db.models import QuerySet, Q, Count, Avg, Sum, Prefetch, Max, Min, Case, When, FloatField
from django.utils import timezone
from typing import Optional, Dict, Any
from django.core.paginator import Paginator
from exam.models import (
    Exam, ExamResult, StudentExamSession, 
    StudentAnswer, OnlineExamResult, Grade
)
from account.models import User

class ExamSelector:
    """Selector for exam-related queries"""

    @staticmethod
    def get_exam_queryset(exam_id: Optional[str] = None) -> QuerySet[Exam]:
        """Base queryset for exams with related data"""
        queryset = Exam.objects.select_related(
            'batch', 'batch__course', 'batch__course__academy', 'published_by', 'created_by'
        ).prefetch_related(
            'results', 'student_sessions'
        ).annotate(
            total_results=Count('results'),
            avg_marks=Avg('results__obtained_marks'),
            max_marks=Max('results__obtained_marks'),
            min_marks=Min('results__obtained_marks'),
            pass_count=Count('results', filter=Q(results__is_passed=True)),
            fail_count=Count('results', filter=Q(results__is_passed=False)),
            # Pass percentage (avoid division by zero)
            pass_percentage=Case(
                When(total_results=0, then=0.0),
                default=Count('results', filter=Q(results__is_passed=True)) * 100.0 / Count('results'),
                output_field=FloatField()
            ),

            # Grade distribution
            grade_a_plus_count=Count('results', filter=Q(results__grade__grade='A+')),
            grade_a_count=Count('results', filter=Q(results__grade__grade='A')),
            grade_a_minus_count=Count('results', filter=Q(results__grade__grade='A-')),
            grade_b_count=Count('results', filter=Q(results__grade__grade='B')),
            grade_c_count=Count('results', filter=Q(results__grade__grade='C')),
            grade_d_count=Count('results', filter=Q(results__grade__grade='D')),
            grade_f_count=Count('results', filter=Q(results__grade__grade='F')),
            
            # Attendance stats
            present_count=Count('results', filter=Q(results__was_present=True)),
            absent_count=Count('results', filter=Q(results__was_present=False)),
        )

        if exam_id:
            queryset = queryset.get(exam_id=exam_id)
        return queryset
    
    @staticmethod
    def get_role_based_exam_queryset(
        queryset: QuerySet[Exam],
        request_user: User
    ) -> QuerySet[Exam]:
        """Get exam queryset based on user role"""

        if request_user.is_student():
            queryset = queryset.filter(
                batch__students=request_user.student,
                is_published=True,
                is_active=True
            )
        elif request_user.is_academy():
            queryset = queryset.filter(
                batch__course__academy=request_user.academy,
                is_active=True
            )
        elif request_user.is_admin():
            queryset = queryset
        else:
            queryset = Exam.objects.none()

        return queryset

    @staticmethod
    def apply_list_filters(
        queryset: QuerySet, filters: Dict[str, Any],
    ) -> QuerySet[Exam]:
        """Get exam queryset with applied filters"""

        if filters.get('batch_id'):
            queryset = queryset.filter(batch_id=filters['batch_id'])
        if filters.get('subject'):
            queryset = queryset.filter(subject=filters['subject'])
        if filters.get('exam_type'):
            queryset = queryset.filter(exam_type=filters['exam_type'])
        # Convert string to boolean for is_published
        if filters.get('is_published'):
            is_published = filters.get('is_published').lower() == 'true'
            queryset = queryset.filter(is_published=is_published)
        if filters.get('is_active'):
            is_active = filters.get('is_active').lower() == 'true'
            queryset = queryset.filter(is_active=is_active)

        return queryset
    
    @staticmethod
    def apply_list_search(
        queryset: QuerySet,
        search_query: str
    ) -> QuerySet[Exam]:
        """Apply search filter to exam queryset"""
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        return queryset

    @staticmethod
    def apply_list_ordering(
        queryset: QuerySet,
        ordering: Optional[str]
    ) -> QuerySet[Exam]:
        """Apply ordering to exam queryset"""
        if ordering:
            if ordering.startswith('-'):
                field = ordering[1:]
                if field in ['id', 'title', 'is_published', 'is_active', 'exam_date', 'results_published', 'result_published_at']:
                    queryset = queryset.order_by(ordering)
            else:
                if ordering in ['id', 'title', 'is_published', 'is_active', 'exam_date', 'results_published', 'result_published_at']:
                    queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('exam_date')  # Default ordering
        
        return queryset
    
    @staticmethod
    def paginate_queryset(queryset, page_size, page):
        """Apply pagination"""
        page_size = int(page_size)
        page_number = int(page)
        
        # Limit page size to prevent abuse
        page_size = min(page_size, 20)
        
        paginator = Paginator(queryset, page_size)
        page = paginator.get_page(page_number)
        
        return {
            'results': page.object_list,
            'pagination': {
                'page': page_number,
                'page_size': page_size,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
                'has_next': page.has_next(),
                'has_previous': page.has_previous(),
                'next_page': page.next_page_number() if page.has_next() else None,
                'previous_page': page.previous_page_number() if page.has_previous() else None,
            }
        }

    @staticmethod
    def list_exams(
        request_user: User,
        filters: Dict[str, Any] = None,
        search_query: Optional[str] = None,
        ordering: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> QuerySet[Exam]:
        """List exams with filters and optimizations"""

        # Get base queryset with optimized joins
        queryset = ExamSelector.get_exam_queryset()

        # Apply role-based filtering
        queryset = ExamSelector.get_role_based_exam_queryset(queryset, request_user)

        # Apply filters
        queryset = ExamSelector.apply_list_filters(queryset, filters)

        # Apply search
        queryset = ExamSelector.apply_list_search(queryset, search_query)

        # Apply ordering
        queryset = ExamSelector.apply_list_ordering(queryset, ordering)

        # Apply pagination
        pagination_info = ExamSelector.paginate_queryset(queryset, page_size, page)

        return pagination_info

    @staticmethod
    def get_exam_by_id(exam_id: str) -> Optional[Exam]:
        """Get exam by exam_id with related data"""
        try:
            return Exam.objects.select_related(
                'batch', 'batch__course', 'batch__course__academy', 'published_by'
            ).get(exam_id=exam_id)
        except Exam.DoesNotExist:
            return None

    @staticmethod
    def get_exam_with_stats(exam_id: str) -> Optional[Exam]:
        """Get exam with comprehensive statistics"""
        try:
            return Exam.objects.select_related(
                'batch', 'batch__course', 'published_by'
            ).prefetch_related(
                Prefetch(
                    'results',
                    queryset=ExamResult.objects.select_related('student__user', 'grade')
                ),
                Prefetch(
                    'student_sessions',
                    queryset=StudentExamSession.objects.select_related('student__user')
                )
            ).annotate(
                total_results=Count('results'),
                average_marks=Avg('results__obtained_marks'),
                pass_count=Count('results', filter=Q(results__is_passed=True))
            ).get(exam_id=exam_id)
        except Exam.DoesNotExist:
            return None

    @staticmethod
    def get_exam_students(exam_id: str) -> QuerySet:
        """Get students enrolled in exam batch"""
        try:
            exam = Exam.objects.get(exam_id=exam_id)
            return exam.batch.students.select_related(
                'user'
            ).filter(
                batchenrollment__is_active=True
            ).order_by('user__first_name', 'user__last_name')
        except Exam.DoesNotExist:
            return []

    @staticmethod
    def can_student_take_exam(exam_id: str, student_id: int) -> bool:
        """Check if student can take the exam"""
        try:
            exam = Exam.objects.get(exam_id=exam_id)
            # Check if student is enrolled in batch
            return exam.batch.students.filter(
                id=student_id,
                batchenrollment__is_active=True
            ).exists()
        except Exam.DoesNotExist:
            return False

    @staticmethod
    def get_upcoming_exams(batch_id: Optional[int] = None, days: int = 7) -> QuerySet[Exam]:
        """Get upcoming exams within specified days"""
        end_date = timezone.now() + timezone.timedelta(days=days)
        queryset = Exam.objects.filter(
            exam_date__gte=timezone.now(),
            exam_date__lte=end_date,
            is_active=True
        ).select_related('batch', 'batch__course')

        if batch_id:
            queryset = queryset.filter(batch_id=batch_id)

        return queryset.order_by('exam_date')

    @staticmethod
    def get_batch_exam_statistics(batch_id: int) -> Dict[str, Any]:
        """Get comprehensive exam statistics for a batch"""
        exams = Exam.objects.filter(batch_id=batch_id).aggregate(
            total_exams=Count('id'),
            published_exams=Count('id', filter=Q(is_published=True)),
            completed_exams=Count('id', filter=Q(exam_date__lt=timezone.now())),
            average_marks=Avg('results__obtained_marks'),
            total_students_appeared=Count('results__student', distinct=True)
        )
        return exams


class ExamResultSelector:
    """Selector for exam result queries"""

    @staticmethod
    def list_exam_results(
        exam_id: Optional[str] = None,
        student_id: Optional[int] = None,
        batch_id: Optional[int] = None,
        is_passed: Optional[bool] = None
    ) -> QuerySet[ExamResult]:
        """List exam results with filters"""
        queryset = ExamResult.objects.select_related(
            'exam', 'exam__batch', 'student', 'student__user', 
            'grade', 'enrollment', 'entered_by'
        )

        if exam_id:
            queryset = queryset.filter(exam__exam_id=exam_id)
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if batch_id:
            queryset = queryset.filter(exam__batch_id=batch_id)
        if is_passed is not None:
            queryset = queryset.filter(is_passed=is_passed)

        return queryset.order_by('-obtained_marks')

    @staticmethod
    def get_result_by_id(result_id: str) -> Optional[ExamResult]:
        """Get exam result by result_id"""
        try:
            return ExamResult.objects.select_related(
                'exam', 'student', 'student__user', 'grade', 
                'entered_by', 'verified_by'
            ).get(result_id=result_id)
        except ExamResult.DoesNotExist:
            return None

    @staticmethod
    def get_student_exam_results(student_id: int, batch_id: Optional[int] = None) -> QuerySet[ExamResult]:
        """Get all exam results for a student"""
        queryset = ExamResult.objects.select_related(
            'exam', 'exam__batch', 'grade'
        ).filter(student_id=student_id)

        if batch_id:
            queryset = queryset.filter(exam__batch_id=batch_id)

        return queryset.order_by('-exam__exam_date')

    @staticmethod
    def get_exam_result_analytics(exam_id: str) -> Dict[str, Any]:
        """Get exam result analytics"""
        try:
            exam = Exam.objects.get(exam_id=exam_id)
            results = ExamResult.objects.filter(exam=exam)
            
            total_students = exam.enrolled_students_count
            results_submitted = results.count()
            
            if results_submitted == 0:
                return {
                    'total_students': total_students,
                    'results_submitted': 0,
                    'pending_results': total_students,
                    'pass_count': 0,
                    'fail_count': 0,
                    'pass_percentage': 0,
                    'average_marks': 0,
                    'highest_marks': 0,
                    'lowest_marks': 0,
                    'grade_distribution': {}
                }

            analytics = results.aggregate(
                pass_count=Count('id', filter=Q(is_passed=True)),
                fail_count=Count('id', filter=Q(is_passed=False)),
                avg_marks=Avg('obtained_marks'),
                max_marks=Max('obtained_marks'),
                min_marks=Min('obtained_marks')
            )

            # Grade distribution
            grade_distribution = {}
            grades = Grade.objects.all()
            for grade in grades:
                count = results.filter(grade=grade).count()
                grade_distribution[grade.grade] = count

            return {
                'total_students': total_students,
                'results_submitted': results_submitted,
                'pending_results': total_students - results_submitted,
                'pass_count': analytics['pass_count'] or 0,
                'fail_count': analytics['fail_count'] or 0,
                'pass_percentage': round((analytics['pass_count'] or 0) / results_submitted * 100, 2) if results_submitted > 0 else 0,
                'average_marks': round(analytics['avg_marks'] or 0, 2),
                'highest_marks': analytics['max_marks'] or 0,
                'lowest_marks': analytics['min_marks'] or 0,
                'grade_distribution': grade_distribution
            }
        except Exam.DoesNotExist:
            return {}

    @staticmethod
    def get_student_exam_history(student_id: int) -> QuerySet[ExamResult]:
        """Get exam history for a student"""
        return ExamResult.objects.select_related(
            'exam',
            'exam__batch',
            'exam__batch__course',
            'grade'
        ).filter(
            student_id=student_id
        ).order_by('-exam__exam_date')

    @staticmethod
    def get_batch_results_summary(batch_id: int) -> Dict[str, Any]:
        """Get results summary for a batch"""
        results = ExamResult.objects.filter(
            exam__batch_id=batch_id
        ).select_related('exam')

        exams = results.values('exam__title', 'exam__exam_id').distinct()
        summary = []

        for exam in exams:
            exam_results = results.filter(exam__exam_id=exam['exam__exam_id'])
            analytics = exam_results.aggregate(
                total_results=Count('id'),
                pass_count=Count('id', filter=Q(is_passed=True)),
                avg_marks=Avg('obtained_marks')
            )
            
            summary.append({
                'exam_title': exam['exam__title'],
                'exam_id': exam['exam__exam_id'],
                'total_results': analytics['total_results'],
                'pass_count': analytics['pass_count'] or 0,
                'pass_percentage': round((analytics['pass_count'] or 0) / analytics['total_results'] * 100, 2) if analytics['total_results'] > 0 else 0,
                'average_marks': round(analytics['avg_marks'] or 0, 2)
            })

        return {'exams': summary}


class StudentExamSessionSelector:
    """Selector for student exam session queries"""

    @staticmethod
    def list_exam_sessions(
        exam_id: Optional[str] = None,
        student_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> QuerySet[StudentExamSession]:
        """List exam sessions with filters"""
        queryset = StudentExamSession.objects.select_related(
            'exam', 'exam__batch', 'student', 'student__user', 'enrollment'
        ).prefetch_related(
            'answers',
            'answers__question',
            'answers__selected_option'
        )

        if exam_id:
            queryset = queryset.filter(exam__exam_id=exam_id)
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('-started_at')

    @staticmethod
    def get_session_by_id(session_id: str) -> Optional[StudentExamSession]:
        """Get session by session_id"""
        try:
            return StudentExamSession.objects.select_related(
                'exam', 'student', 'student__user', 'enrollment'
            ).prefetch_related(
                'answers__question',
                'answers__selected_option'
            ).get(session_id=session_id)
        except StudentExamSession.DoesNotExist:
            return None

    @staticmethod
    def get_active_session(exam_id: str, student_id: int) -> Optional[StudentExamSession]:
        """Get active session for student in exam"""
        try:
            return StudentExamSession.objects.select_related(
                'exam', 'student'
            ).filter(
                exam__exam_id=exam_id,
                student_id=student_id,
                status='in_progress'
            ).first()
        except StudentExamSession.DoesNotExist:
            return None

    @staticmethod
    def get_session_statistics(exam_id: str) -> Dict[str, Any]:
        """Get session statistics for an exam"""
        sessions = StudentExamSession.objects.filter(exam__exam_id=exam_id)
        
        stats = sessions.aggregate(
            total_sessions=Count('id'),
            completed_sessions=Count('id', filter=Q(status='submitted')),
            in_progress_sessions=Count('id', filter=Q(status='in_progress')),
            timeout_sessions=Count('id', filter=Q(status='timeout')),
            average_time_spent=Avg('time_spent_minutes')
        )
        
        return stats


class StudentAnswerSelector:
    """Selector for student answer queries"""

    @staticmethod
    def list_session_answers(session_id: str) -> QuerySet[StudentAnswer]:
        """Get all answers for a session"""
        return StudentAnswer.objects.select_related(
            'session',
            'question',
            'selected_option',
            'graded_by'
        ).filter(
            session__session_id=session_id
        ).order_by('question__question_order')

    @staticmethod
    def get_answer_by_id(answer_id: int) -> Optional[StudentAnswer]:
        """Get answer by ID"""
        try:
            return StudentAnswer.objects.select_related(
                'session', 'session__student', 'question', 
                'selected_option', 'graded_by'
            ).get(id=answer_id)
        except StudentAnswer.DoesNotExist:
            return None
        
    @staticmethod
    def get_session_answer_for_question(session_id: str, question_id: int) -> Optional[StudentAnswer]:
        """Get answer for specific question in session"""
        try:
            return StudentAnswer.objects.get(
                session__session_id=session_id,
                question_id=question_id
            )
        except StudentAnswer.DoesNotExist:
            return None

    @staticmethod
    def get_ungraded_answers(exam_id: Optional[str] = None) -> QuerySet[StudentAnswer]:
        """Get answers that need manual grading"""
        queryset = StudentAnswer.objects.select_related(
            'session', 'session__student', 'session__student__user', 
            'question', 'session__exam'
        ).filter(
            question__question_type__in=['short_answer', 'essay'],
            is_graded=False
        )

        if exam_id:
            queryset = queryset.filter(session__exam__exam_id=exam_id)

        return queryset.order_by('session__exam', 'session__student')


class OnlineExamResultSelector:
    """Selector for online exam result queries"""

    @staticmethod
    def list_online_exam_results(
        exam_id: Optional[str] = None,
        student_id: Optional[int] = None,
        requires_manual_grading: Optional[bool] = None
    ) -> QuerySet[OnlineExamResult]:
        """List online exam results with filters"""
        queryset = OnlineExamResult.objects.select_related(
            'exam',
            'exam__batch',
            'student',
            'student__user',
            'session',
            'grade'
        )

        if exam_id:
            queryset = queryset.filter(exam__exam_id=exam_id)
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if requires_manual_grading is not None:
            if requires_manual_grading:
                queryset = queryset.filter(is_manual_grading_complete=False)
            else:
                queryset = queryset.filter(is_manual_grading_complete=True)
        return queryset.order_by('-session__obtained_marks')

    @staticmethod
    def get_online_result_by_session(session_id: str) -> Optional[OnlineExamResult]:
        """Get online exam result by session"""
        try:
            return OnlineExamResult.objects.select_related(
                'exam',
                'exam__batch',
                'student',
                'student__user',
                'session',
                'grade'
            ).prefetch_related(
                'session__answers',
                'session__answers__question',
                'session__answers__selected_option'
            ).get(session__session_id=session_id)
        except OnlineExamResult.DoesNotExist:
            return None