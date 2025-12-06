from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save
from django.dispatch import receiver
from exam.utils import IDGenerator
from classmate.models import ClassMateModel
from academy.choices_fields import SUBJECT_TYPE_CHOICES, SUBJECT_TYPE_BANGLA
from academy.models import Batch, BatchEnrollment
from account.models import User
from exam.choices import EXAM_TYPE_CHOICES, PAPER_BASED


class Grade(models.Model):
    GRADE_CHOICES = [
        ('A+', 'A+'),
        ('A', 'A'),
        ('A-', 'A-'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
        ('F', 'F'),
    ]

    grade = models.CharField(max_length=2, choices=GRADE_CHOICES, unique=True)

    def __str__(self):
        return self.grade


class Exam(ClassMateModel):
    """Model to represent batch-wise exams"""
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='exams')
    subject = models.CharField(
        max_length=50,
        choices=SUBJECT_TYPE_CHOICES,
        default=SUBJECT_TYPE_BANGLA,
        help_text="Subject"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    exam_date = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField()
    total_marks = models.DecimalField(max_digits=6, decimal_places=2)
    pass_marks = models.DecimalField(max_digits=6, decimal_places=2)
    exam_id = models.CharField(max_length=40, unique=True, help_text='Unique ID for the Exam', editable=False, null=True, blank=True)

    exam_type = models.CharField(max_length=10, choices=EXAM_TYPE_CHOICES, default=PAPER_BASED, help_text='Type of exam')
    is_published = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Result management
    results_published = models.BooleanField(default=False)
    result_published_at = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='published_exams')
    
    # Notification tracking
    sms_sent = models.BooleanField(default=False)
    sms_sent_at = models.DateTimeField(null=True, blank=True)
    app_notification_sent = models.BooleanField(default=False)
    app_notification_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Exam'
        verbose_name_plural = 'Exams'
        ordering = ['-exam_date']
        constraints = [
            models.UniqueConstraint(fields=['batch', 'title'], name='unique_exam_title_per_batch'),
        ]

    def __str__(self):
        return f'{self.title} - {self.batch.name} ({self.get_exam_type_display()})'

    def clean(self):
        """Validate exam data"""
        from django.utils import timezone
        
        if self.pass_marks and self.total_marks and self.pass_marks > self.total_marks:
            raise ValidationError('Pass marks cannot be greater than total marks.')
        
        if not self.pk and self.exam_date and self.exam_date < timezone.now():
            raise ValidationError('Exam date cannot be in the past.')

    @property
    def is_completed(self):
        """Check if exam is completed based on current time"""
        from django.utils import timezone
        return self.exam_date is not None and timezone.now() > self.exam_date

    @property
    def can_publish_results(self):
        """Check if results can be published"""
        return self.is_completed and not self.results_published

    @property
    def enrolled_students_count(self):
        """Get count of enrolled students in the batch"""
        return self.batch.students.filter(
            batchenrollment__is_active=True
        ).count()

    @property
    def results_submitted_count(self):
        """Get count of results already submitted"""
        return self.results.count()

    @property
    def pending_results_count(self):
        """Get count of pending results to be entered"""
        return self.enrolled_students_count - self.results_submitted_count


class ExamResult(ClassMateModel):
    """Model to store individual student exam results"""
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='results')
    student = models.ForeignKey('student.Student', on_delete=models.CASCADE, related_name='exam_results')
    enrollment = models.ForeignKey(BatchEnrollment, on_delete=models.CASCADE, related_name='exam_results')
    
    # Result details
    obtained_marks = models.DecimalField(max_digits=6, decimal_places=2)
    grade = models.ForeignKey(Grade, on_delete=models.SET_NULL, null=True, blank=True)
    is_passed = models.BooleanField(default=False)
    
    # Attendance and submission tracking
    was_present = models.BooleanField(default=True)

    # Result entry tracking (for paper-based exams)
    entered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='entered_results')
    entered_at = models.DateTimeField(auto_now_add=True)
    last_modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modified_results')
    last_modified_at = models.DateTimeField(auto_now=True)

    # Additional details
    remarks = models.TextField(blank=True)
    result_id = models.CharField(max_length=40, unique=True, editable=False, null=True, blank=True)

    # Verification status (for quality control)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_results')
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Exam Result'
        verbose_name_plural = 'Exam Results'
        ordering = ['-obtained_marks']
        constraints = [
            models.UniqueConstraint(fields=['exam', 'student'], name='unique_result_per_exam_student'),
        ]

    def __str__(self):
        return f'{self.student.user.get_full_name()} - {self.exam.title} - {self.obtained_marks}/{self.exam.total_marks}'

    def clean(self):
        """Validate result data"""
        # Ensure student is enrolled in the batch for this exam
        if self.student and self.exam:
            try:
                enrollment = BatchEnrollment.objects.get(
                    student=self.student, 
                    batch=self.exam.batch,
                    is_active=True
                )
                self.enrollment = enrollment
            except BatchEnrollment.DoesNotExist:
                raise ValidationError(f'Student {self.student} is not enrolled in batch {self.exam.batch}.')
        
        # Validate obtained marks
        if self.obtained_marks and self.exam and self.obtained_marks > self.exam.total_marks:
            raise ValidationError('Obtained marks cannot be greater than total marks.')

    def save(self, *args, **kwargs):
        """Auto-calculate pass/fail status and grade"""
        # Call clean() to ensure validation
        self.full_clean()

        # Auto-calculate pass/fail status
        if self.exam and self.obtained_marks is not None:
            self.is_passed = self.obtained_marks >= self.exam.pass_marks
        
        # Auto-assign grade based on percentage
        if self.exam and self.obtained_marks is not None:
            percentage = (self.obtained_marks / self.exam.total_marks) * 100
            self.grade = self._calculate_grade(percentage)
        
        super().save(*args, **kwargs)

    def _calculate_grade(self, percentage: float):
        """Calculate grade based on percentage"""
        try:
            if percentage >= 90:
                return Grade.objects.get(grade='A+')
            elif percentage >= 80:
                return Grade.objects.get(grade='A')
            elif percentage >= 70:
                return Grade.objects.get(grade='A-')
            elif percentage >= 60:
                return Grade.objects.get(grade='B')
            elif percentage >= 50:
                return Grade.objects.get(grade='C')
            elif percentage >= 40:
                return Grade.objects.get(grade='D')
            else:
                return Grade.objects.get(grade='F')
        except Grade.DoesNotExist:
            return None

    @property
    def percentage(self):
        """Calculate percentage score"""
        if self.exam and self.obtained_marks is not None:
            return round((self.obtained_marks / self.exam.total_marks) * 100, 2)
        return 0

    @property
    def status(self):
        """Return pass/fail status as string"""
        return 'Passed' if self.is_passed else 'Failed'


class StudentExamSession(ClassMateModel):
    """Model to track student exam sessions for online exams"""
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='student_sessions')
    student = models.ForeignKey('student.Student', on_delete=models.CASCADE, related_name='exam_sessions')
    enrollment = models.ForeignKey(BatchEnrollment, on_delete=models.CASCADE, related_name='exam_sessions')
    
    # Session tracking
    session_id = models.CharField(max_length=50, unique=True, help_text='Unique session identifier')
    started_at = models.DateTimeField(auto_now_add=True, help_text='When student started the exam')
    submitted_at = models.DateTimeField(null=True, blank=True, help_text='When student submitted the exam')
    last_activity_at = models.DateTimeField(auto_now=True, help_text='Last activity timestamp')
    
    # Session status
    SESSION_STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('timeout', 'Timed Out'),
        ('interrupted', 'Interrupted'),
    ]
    status = models.CharField(max_length=15, choices=SESSION_STATUS_CHOICES, default='in_progress')
    
    # Time tracking
    time_spent_minutes = models.PositiveIntegerField(default=0, help_text='Total time spent in minutes')
    is_time_extended = models.BooleanField(default=False, help_text='Whether extra time was granted')
    extended_time_minutes = models.PositiveIntegerField(default=0, help_text='Extra time granted in minutes')
    
    # Technical tracking
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text='Student IP address')
    user_agent = models.TextField(blank=True, help_text='Browser/device information')
    
    class Meta:
        verbose_name = 'Student Exam Session'
        verbose_name_plural = 'Student Exam Sessions'
        ordering = ['-started_at']
        constraints = [
            models.UniqueConstraint(fields=['exam', 'student'], name='unique_session_per_exam_student')
        ]

    def __str__(self):
        return f'{self.student.user.get_full_name()} - {self.exam.title} ({self.get_status_display()})'

    @property
    def is_active(self):
        """Check if session is still active"""
        return self.status == 'in_progress'

    @property
    def total_allowed_minutes(self):
        """Get total allowed time including extensions"""
        return self.exam.duration_minutes + self.extended_time_minutes

    @property
    def remaining_minutes(self):
        """Calculate remaining time"""
        if self.status != 'in_progress':
            return 0
        return max(0, self.total_allowed_minutes - self.time_spent_minutes)

    @property
    def is_timeout(self):
        """Check if session has timed out"""
        return self.time_spent_minutes >= self.total_allowed_minutes


class StudentAnswer(ClassMateModel):
    """Model to store student answers for online exams"""
    session = models.ForeignKey(StudentExamSession, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey('question.Question', on_delete=models.CASCADE, related_name='student_answers')
    
    # Answer content
    selected_option = models.ForeignKey('question.QuestionOption', on_delete=models.CASCADE, null=True, blank=True, related_name='student_selections')
    text_answer = models.TextField(blank=True, help_text='Text answer for short answer/essay questions')
    
    # Answer metadata
    answered_at = models.DateTimeField(auto_now_add=True, help_text='When answer was submitted')
    last_modified_at = models.DateTimeField(auto_now=True, help_text='When answer was last modified')
    
    # Scoring (for auto-graded questions)
    is_correct = models.BooleanField(null=True, blank=True, help_text='Whether answer is correct (auto-calculated for MCQ)')
    awarded_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text='Marks awarded for this answer')
    
    # Manual grading (for essay/short answer)
    is_graded = models.BooleanField(default=False, help_text='Whether answer has been manually graded')
    graded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='graded_answers')
    graded_at = models.DateTimeField(null=True, blank=True, help_text='When answer was graded')
    grader_remarks = models.TextField(blank=True, help_text='Grader comments/feedback')

    class Meta:
        verbose_name = 'Student Answer'
        verbose_name_plural = 'Student Answers'
        ordering = ['session', 'question__question_order']
        constraints = [
            models.UniqueConstraint(fields=['session', 'question'], name='unique_answer_per_session_question')
        ]

    def __str__(self):
        return f'{self.session.student.user.get_full_name()} - Q{self.question.question_order}'

    def clean(self):
        """Validate answer data"""
        if self.question.question_type in ['mcq', 'true_false'] and not self.selected_option:
            raise ValidationError('Selected option is required for MCQ/True-False questions.')
        
        if self.question.question_type in ['short_answer', 'essay'] and not self.text_answer.strip():
            raise ValidationError('Text answer is required for short answer/essay questions.')

    def save(self, *args, **kwargs):
        """Auto-grade MCQ/True-False questions"""
        if self.question.question_type in ['mcq', 'true_false'] and self.selected_option:
            self.is_correct = self.selected_option.is_correct
            self.awarded_marks = self.question.marks if self.is_correct else 0
            self.is_graded = True
        
        super().save(*args, **kwargs)


class OnlineExamResult(ExamResult):
    """Extended result model for online exams with additional tracking"""
    session = models.OneToOneField(StudentExamSession, on_delete=models.CASCADE, related_name='result')
    
    # Auto-scoring details
    auto_graded_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0, help_text='Marks from auto-graded questions')
    manual_graded_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0, help_text='Marks from manually graded questions')
    
    # Completion tracking
    total_questions_attempted = models.PositiveIntegerField(default=0, help_text='Number of questions attempted')
    total_questions = models.PositiveIntegerField(default=0, help_text='Total number of questions in exam')
    
    # Processing status
    is_auto_processed = models.BooleanField(default=False, help_text='Whether auto-grading is complete')
    is_manual_grading_complete = models.BooleanField(default=False, help_text='Whether manual grading is complete')
    
    class Meta:
        verbose_name = 'Online Exam Result'
        verbose_name_plural = 'Online Exam Results'

    def save(self, *args, **kwargs):
        """Calculate total obtained marks from auto and manual grading"""
        self.obtained_marks = self.auto_graded_marks + self.manual_graded_marks
        super().save(*args, **kwargs)

    @property
    def completion_percentage(self):
        """Calculate exam completion percentage"""
        if self.total_questions > 0:
            return round((self.total_questions_attempted / self.total_questions) * 100, 2)
        return 0

    @property
    def requires_manual_grading(self):
        """Check if result requires manual grading"""
        return not self.is_manual_grading_complete and self.session.answers.filter(
            question__question_type__in=['short_answer', 'essay'],
            is_graded=False
        ).exists()


# Add signals for auto-generating IDs
@receiver(pre_save, sender=Exam)
def set_exam_id_on_create(sender, instance, **kwargs):
    """Signal to auto-generate exam_id only when creating a new Exam."""
    if (not instance.pk and not instance.exam_id) or (instance.pk and not instance.exam_id):
        instance.exam_id = IDGenerator.generate_exam_id()


@receiver(pre_save, sender=ExamResult)
def set_result_id_on_create(sender, instance, **kwargs):
    """Signal to auto-generate result_id only when creating a new ExamResult."""
    if (not instance.pk and not instance.result_id) or (instance.pk and not instance.result_id):
        instance.result_id = IDGenerator.generate_result_id()


@receiver(pre_save, sender=StudentExamSession)
def generate_session_id(sender, instance, **kwargs):
    """Generate unique session ID"""
    if not instance.session_id:
        import uuid
        instance.session_id = str(uuid.uuid4())

