from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from typing import Dict, Any, Optional, List
from decimal import Decimal
from django.db import transaction, IntegrityError
from exam.models import (
    Exam, ExamResult, StudentExamSession, 
    StudentAnswer, OnlineExamResult, Grade
)
from academy.models import Batch, BatchEnrollment
from student.models import Student
from account.models import User
from django.http import HttpResponse
from django.db.models import Sum
import csv
import uuid
from exam.selectors import exam_selector

class ExamService:
    """Service for exam operations"""

    @staticmethod
    @transaction.atomic
    def create_exam(data: Dict[str, Any], user: User) -> Exam:
        """Create a new exam"""
        # Validate batch exists and user has permission
        try:
            if user.is_academy():
                try:
                    batch = Batch.objects.get(id=data['batch_id'], course__academy=user.academy)
                except Batch.DoesNotExist:
                    raise ValidationError('Batch not found or access denied')
            elif user.is_admin():
                try:
                    batch = Batch.objects.get(id=data['batch_id'])
                except Batch.DoesNotExist:
                    raise ValidationError('Batch not found')
            else:
                raise ValidationError('User does not have permission to create exam')
        except Batch.DoesNotExist:
            raise ValidationError('Batch not found')

        try:
            exam = Exam.objects.create(
                created_by=user,
                batch=batch,
                subject=data['subject'],
                title=data['title'],
                description=data.get('description', ''),
                exam_date=data['exam_date'],
                duration_minutes=data['duration_minutes'],
                total_marks=data['total_marks'],
                pass_marks=data['pass_marks'],
                exam_type=data.get('exam_type', 'paper')
            )
        except IntegrityError as e:
            if 'unique_exam_title_per_batch' in str(e):
                raise ValidationError("An exam with the same title already exists for this batch.")
            raise
        except Exception as e:
            raise
        return exam

    @staticmethod
    @transaction.atomic
    def update_exam(exam_id: str, data: Dict[str, Any], user: User) -> Exam:
        """Update an existing exam"""
        exam = exam_selector.ExamSelector.get_exam_by_id(exam_id)
        if not exam:
            raise ValidationError('Exam not found')

        # Validate user has permission
        try:
            if user.is_academy():
                try:
                    if exam.batch.course.academy != user.academy:
                        raise ValidationError('Access denied')
                except:
                    raise ValidationError('Access denied')
            elif user.is_admin():
                pass
            else:
                raise ValidationError('User does not have permission to update exam')
        except:
            raise ValidationError('Access denied')

        # Don't allow updating if exam is completed
        if exam.is_completed:
            raise ValidationError('Cannot update completed exam')

        for field, value in data.items():
            if hasattr(exam, field):
                setattr(exam, field, value)

        # Set modified_by field if it exists on the model
        if hasattr(exam, 'modified_by'):
            exam.modified_by = user

        exam.full_clean()
        exam.save()
        return exam

    @staticmethod
    @transaction.atomic
    def publish_exam(exam_id: str, user: User) -> Exam:
        """Publish an exam"""
        exam = exam_selector.ExamSelector.get_exam_by_id(exam_id)
        if not exam:
            raise ValidationError('Exam not found')

        if exam.is_published:
            raise ValidationError('Exam is already published')

        exam.is_published = True
        exam.save()
        return exam

    @staticmethod
    @transaction.atomic
    def publish_results(exam_id: str, user: User) -> Exam:
        """Publish exam results"""
        exam = exam_selector.ExamSelector.get_exam_by_id(exam_id)
        if not exam:
            raise ValidationError('Exam not found')

        if not exam.can_publish_results:
            raise ValidationError('Cannot publish results for this exam')

        exam.results_published = True
        exam.result_published_at = timezone.now()
        exam.published_by = user
        exam.save()

        # TODO: Send notifications to students
        ExamService._send_result_notifications(exam)
        
        return exam

    @staticmethod
    @transaction.atomic
    def delete_exam(exam_id: str, user: User) -> bool:
        """Delete an exam (soft delete by marking inactive)"""
        exam = exam_selector.ExamSelector.get_exam_by_id(exam_id)
        if not exam:
            raise ValidationError('Exam not found')
        
        # Validate user has permission
        try:
            if user.is_academy():
                try:
                    if exam.batch.course.academy != user.academy:
                        raise ValidationError('Access denied')
                except:
                    raise ValidationError('Access denied')
            elif user.is_admin():
                pass
            else:
                raise ValidationError('User does not have permission to update exam')
        except:
            raise ValidationError('Access denied')

        if exam.results.exists():
            raise ValidationError('Cannot delete exam with existing results')

        exam.is_active = False

        # Set modified_by field if it exists on the model
        if hasattr(exam, 'modified_by'):
            exam.modified_by = str(user)

        # Set modified_by field if it exists on the model
        if hasattr(exam, 'archived_at'):
            exam.archived_at = timezone.now()

        exam.title = f"{exam.title} - Archived"
        exam.save()
        return True

    @staticmethod
    def _send_result_notifications(exam: Exam) -> None:
        """Send result notifications to students"""
        # TODO: Implement notification logic
        pass


class ExamResultService:
    """Service for exam result operations"""

    @staticmethod
    @transaction.atomic
    def create_result(data: Dict[str, Any], user: User) -> ExamResult:
        """Create an exam result"""
        try:
            exam = Exam.objects.get(exam_id=data['exam_id'])
            student = Student.objects.get(id=data['student_id'])
        except (Exam.DoesNotExist, Student.DoesNotExist):
            raise ValidationError('Exam or Student not found')

        # Check if result already exists
        if ExamResult.objects.filter(exam=exam, student=student).exists():
            raise ValidationError('Result already exists for this student and exam')

        result = ExamResult.objects.create(
            exam=exam,
            student=student,
            obtained_marks=data['obtained_marks'],
            was_present=data.get('was_present', True),
            entered_by=user,
            remarks=data.get('remarks', '')
        )
        return result

    @staticmethod
    @transaction.atomic
    def update_result(result_id: str, data: Dict[str, Any], user: User) -> ExamResult:
        """Update an exam result"""
        result = exam_selector.ExamResultSelector.get_result_by_id(result_id)
        if not result:
            raise ValidationError('Result not found')

        if result.exam.results_published:
            raise ValidationError('Cannot update published results')

        # Update fields
        if 'obtained_marks' in data:
            result.obtained_marks = data['obtained_marks']
        if 'was_present' in data:
            result.was_present = data['was_present']
        if 'remarks' in data:
            result.remarks = data['remarks']

        result.last_modified_by = user
        result.last_modified_at = timezone.now()
        result.full_clean()
        result.save()
        return result

    @staticmethod
    @transaction.atomic
    def bulk_create_results(exam_id: str, results_data: List[Dict[str, Any]], user: User) -> List[ExamResult]:
        """Bulk create exam results"""
        exam = exam_selector.ExamSelector.get_exam_by_id(exam_id)
        if not exam:
            raise ValidationError('Exam not found')

        results = []
        for data in results_data:
            try:
                student = Student.objects.get(id=data['student_id'])
                
                # Skip if result already exists
                if ExamResult.objects.filter(exam=exam, student=student).exists():
                    continue

                result = ExamResult(
                    exam=exam,
                    student=student,
                    obtained_marks=data['obtained_marks'],
                    was_present=data.get('was_present', True),
                    entered_by=user,
                    remarks=data.get('remarks', '')
                )
                results.append(result)
            except Student.DoesNotExist:
                continue

        ExamResult.objects.bulk_create(results)
        return results

    @staticmethod
    @transaction.atomic
    def verify_result(result_id: str, user: User) -> ExamResult:
        """Verify an exam result"""
        result = exam_selector.ExamResultSelector.get_result_by_id(result_id)
        if not result:
            raise ValidationError('Result not found')

        result.is_verified = True
        result.verified_by = user
        result.verified_at = timezone.now()
        result.save()
        return result
    
    @staticmethod
    @transaction.atomic
    def unverify_result(result_id: str) -> ExamResult:
        """Unverify an exam result"""
        result = exam_selector.ExamResultSelector.get_result_by_id(result_id)
        if not result:
            raise ValidationError('Result not found')

        result.is_verified = False
        result.verified_by = None
        result.verified_at = None
        result.save()
        return result

    @staticmethod
    @transaction.atomic
    def delete_result(result_id: str, user: User) -> bool:
        """Delete an exam result"""
        result = exam_selector.ExamResultSelector.get_result_by_id(result_id)
        if not result:
            raise ValidationError('Result not found')

        if result.exam.results_published:
            raise ValidationError('Cannot delete published results')

        result.delete()
        return True
    
    @staticmethod
    def export_results_csv(exam_id: str) -> HttpResponse:
        """Export exam results to CSV"""
        exam = exam_selector.ExamSelector.get_exam_by_id(exam_id)
        if not exam:
            raise ValidationError('Exam not found')

        results = exam_selector.ExamResultSelector.list_exam_results(exam_id=exam_id)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{exam.title}_results.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Student Name', 'Student ID', 'Obtained Marks', 'Total Marks',
            'Percentage', 'Grade', 'Status', 'Present'
        ])

        for result in results:
            writer.writerow([
                result.student.user.get_full_name(),
                result.student.student_id,
                result.obtained_marks,
                result.exam.total_marks,
                result.percentage,
                result.grade.grade if result.grade else '',
                result.status,
                'Yes' if result.was_present else 'No'
            ])

        return response

    @staticmethod
    def export_results_excel(exam_id: str) -> HttpResponse:
        """Export exam results to Excel"""
        # Implementation would require openpyxl or xlswriter
        # For now, fallback to CSV
        return ExamResultService.export_results_csv(exam_id)


class StudentExamSessionService:
    """Service for student exam session operations"""

    @staticmethod
    @transaction.atomic
    def start_exam_session(exam_id: str, student_id: int, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> StudentExamSession:
        """Start a new exam session"""
        try:
            exam = Exam.objects.get(exam_id=exam_id)
            student = Student.objects.get(id=student_id)
        except (Exam.DoesNotExist, Student.DoesNotExist):
            raise ValidationError('Exam or Student not found')

        if exam.exam_type != 'online':
            raise ValidationError('This is not an online exam')

        if not exam.is_published:
            raise ValidationError('Exam is not published')
        
        # Check if student can take exam
        if not exam_selector.ExamSelector.can_student_take_exam(exam_id, student_id):
            raise ValidationError('Student is not enrolled in this exam batch')

        # Check if student is enrolled
        try:
            enrollment = BatchEnrollment.objects.get(
                student=student,
                batch=exam.batch,
                is_active=True
            )
        except BatchEnrollment.DoesNotExist:
            raise ValidationError('Student is not enrolled in this batch')

        # Check if session already exists
        existing_session = exam_selector.StudentExamSessionSelector.get_active_session(exam_id, student_id)
        if existing_session:
            return existing_session

        # Create new session
        session = StudentExamSession.objects.create(
            exam=exam,
            student=student,
            enrollment=enrollment,
            session_id=str(uuid.uuid4()),
            ip_address=ip_address,
            user_agent=user_agent or ''
        )
        return session

    @staticmethod
    @transaction.atomic
    def submit_exam_session(session_id: str) -> StudentExamSession:
        """Submit an exam session"""
        session = exam_selector.StudentExamSessionSelector.get_session_by_id(session_id)
        if not session:
            raise ValidationError('Session not found')

        if session.status != 'in_progress':
            raise ValidationError('Session is not in progress')

        session.status = 'submitted'
        session.submitted_at = timezone.now()
        session.save()

        # Auto-create online exam result
        # OnlineExamResultService.create_from_session(session)
        
        return session

    @staticmethod
    @transaction.atomic
    def update_session_time(session_id: str, time_spent_minutes: Optional[int] = None) -> StudentExamSession:
        """Update session time spent"""
        session = exam_selector.StudentExamSessionSelector.get_session_by_id(session_id)
        if not session:
            raise ValidationError('Session not found')

        if session.status != 'in_progress':
            raise ValidationError('Session is not active')

        if time_spent_minutes is not None:
            session.time_spent_minutes = time_spent_minutes

        # Check for timeout
        if session.is_timeout:
            session.status = 'timeout'
            session.submitted_at = timezone.now()

        session.save()
        return session

    @staticmethod
    @transaction.atomic
    def extend_exam_session_time(session_id: str, extra_minutes: int, user: User) -> StudentExamSession:
        """Extend session time"""
        session = exam_selector.StudentExamSessionSelector.get_session_by_id(session_id)
        if not session:
            raise ValidationError('Session not found')

        session.is_time_extended = True
        session.extended_time_minutes += extra_minutes
        session.save()
        return session
    
    @staticmethod
    @transaction.atomic
    def update_session_status(
        session_id: str, 
        status: str, 
        time_spent_minutes: Optional[int] = None
    ) -> StudentExamSession:
        """Update session status"""
        session = exam_selector.StudentExamSessionSelector.get_session_by_id(session_id)
        if not session:
            raise ValidationError('Session not found')

        session.status = status
        if time_spent_minutes is not None:
            session.time_spent_minutes = time_spent_minutes
        session.save()
        return session


class StudentAnswerService:
    """Service for student answer operations"""

    @staticmethod
    @transaction.atomic
    def save_answer(session_id: str, question_id: int, answer_data: Dict[str, Any]) -> StudentAnswer:
        """Save or update a student answer"""
        session = exam_selector.StudentExamSessionSelector.get_session_by_id(session_id)
        if not session:
            raise ValidationError('Session not found')

        if session.status != 'in_progress':
            raise ValidationError('Session is not active')

        # Get or create answer
        answer, created = StudentAnswer.objects.get_or_create(
            session=session,
            question_id=question_id,
            defaults=answer_data
        )

        if not created:
            # Update existing answer
            for field, value in answer_data.items():
                if hasattr(answer, field):
                    setattr(answer, field, value)

        answer.full_clean()
        answer.save()
        return answer

    @staticmethod
    @transaction.atomic
    def grade_answer(answer_id: int, awarded_marks: Decimal, remarks: str, user: User) -> StudentAnswer:
        """Manually grade an answer"""
        answer = exam_selector.StudentAnswerSelector.get_answer_by_id(answer_id)
        if not answer:
            raise ValidationError('Answer not found')

        if answer.question.question_type not in ['short_answer', 'essay']:
            raise ValidationError('This answer type cannot be manually graded')

        answer.awarded_marks = awarded_marks
        answer.grader_remarks = remarks
        answer.is_graded = True
        answer.graded_by = user
        answer.graded_at = timezone.now()
        answer.save()

        # Update online exam result if all answers are graded
        StudentAnswerService._update_online_result_if_complete(answer.session)
        
        return answer

    @staticmethod
    def _update_online_result_if_complete(session: StudentExamSession) -> None:
        """Update online exam result when all manual grading is complete"""
        ungraded_count = session.answers.filter(
            question__question_type__in=['short_answer', 'essay'],
            is_graded=False
        ).count()

        if ungraded_count == 0:
            try:
                result = OnlineExamResult.objects.get(session=session)
                result.is_manual_grading_complete = True
                
                # Recalculate manual graded marks
                manual_marks = session.answers.filter(
                    question__question_type__in=['short_answer', 'essay']
                ).aggregate(total=Sum('awarded_marks'))['total'] or 0
                
                result.manual_graded_marks = manual_marks
                result.save()
            except OnlineExamResult.DoesNotExist:
                pass


class OnlineExamResultService:
    """Service for online exam result operations"""

    @staticmethod
    @transaction.atomic
    def create_from_session(session: StudentExamSession) -> OnlineExamResult:
        """Create online exam result from session"""
        # Calculate auto-graded marks
        auto_graded_marks = session.answers.filter(
            question__question_type__in=['mcq', 'true_false'],
            is_correct=True
        ).aggregate(total=Sum('awarded_marks'))['total'] or 0

        # Calculate manual graded marks (if any)
        manual_graded_marks = session.answers.filter(
            question__question_type__in=['short_answer', 'essay'],
            is_graded=True
        ).aggregate(total=Sum('awarded_marks'))['total'] or 0

        # Count questions
        total_questions = session.exam.questions.count()  # Assuming exam has questions
        attempted_questions = session.answers.count()

        # Check if manual grading is complete
        ungraded_answers = session.answers.filter(
            question__question_type__in=['short_answer', 'essay'],
            is_graded=False
        ).exists()

        result = OnlineExamResult.objects.create(
            exam=session.exam,
            student=session.student,
            enrollment=session.enrollment,
            session=session,
            auto_graded_marks=auto_graded_marks,
            manual_graded_marks=manual_graded_marks,
            total_questions=total_questions,
            total_questions_attempted=attempted_questions,
            is_auto_processed=True,
            is_manual_grading_complete=not ungraded_answers
        )

        return result

    @staticmethod
    @transaction.atomic
    def recalculate_result(session_id: str) -> OnlineExamResult:
        """Recalculate online exam result"""
        session = exam_selector.StudentExamSessionSelector.get_session_by_id(session_id)
        if not session:
            raise ValidationError('Session not found')

        try:
            result = OnlineExamResult.objects.get(session=session)
        except OnlineExamResult.DoesNotExist:
            raise ValidationError('Result not found')

        # Recalculate marks
        auto_marks = session.answers.filter(
            question__question_type__in=['mcq', 'true_false'],
            is_correct=True
        ).aggregate(total=Sum('awarded_marks'))['total'] or 0

        manual_marks = session.answers.filter(
            question__question_type__in=['short_answer', 'essay'],
            is_graded=True
        ).aggregate(total=Sum('awarded_marks'))['total'] or 0

        result.auto_graded_marks = auto_marks
        result.manual_graded_marks = manual_marks
        result.save()

        return result

    @staticmethod
    @transaction.atomic
    def process_exam_result(session_id: str) -> OnlineExamResult:
        """Process online exam result after submission"""
        session = exam_selector.StudentExamSessionSelector.get_session_by_id(session_id)
        if not session:
            raise ValidationError('Session not found')

        if session.status != 'submitted':
            raise ValidationError('Session must be submitted first')

        # Check if result already exists
        existing_result = exam_selector.OnlineExamResultSelector.get_result_by_session(session_id)
        if existing_result:
            return existing_result

        # Calculate auto-graded marks
        auto_graded_marks = session.answers.filter(
            is_graded=True
        ).aggregate(
            total=Sum('awarded_marks')
        )['total'] or Decimal('0')

        # Count questions
        total_questions = session.answers.count()
        total_questions_attempted = session.answers.exclude(
            selected_option__isnull=True,
            text_answer=''
        ).count()

        # Get enrollment
        try:
            enrollment = BatchEnrollment.objects.get(
                student=session.student,
                batch=session.exam.batch,
                is_active=True
            )
        except BatchEnrollment.DoesNotExist:
            raise ValidationError('Student enrollment not found')

        result = OnlineExamResult.objects.create(
            exam=session.exam,
            student=session.student,
            enrollment=enrollment,
            session=session,
            auto_graded_marks=auto_graded_marks,
            total_questions=total_questions,
            total_questions_attempted=total_questions_attempted,
            is_auto_processed=True,
            entered_by=None  # Auto-processed
        )

        return result

    @staticmethod
    @transaction.atomic
    def complete_manual_grading(result_id: str, user: User) -> OnlineExamResult:
        """Mark manual grading as complete"""
        result = exam_selector.OnlineExamResultSelector.get_online_result_by_id(result_id)
        if not result:
            raise ValidationError('Result not found')

        # Calculate manual graded marks
        manual_graded_marks = result.session.answers.filter(
            question__question_type__in=['short_answer', 'essay'],
            is_graded=True
        ).aggregate(
            total=Sum('awarded_marks')
        )['total'] or Decimal('0')

        result.manual_graded_marks = manual_graded_marks
        result.is_manual_grading_complete = True
        result.last_modified_by = user
        result.save()  # This will trigger the obtained_marks calculation

        return result