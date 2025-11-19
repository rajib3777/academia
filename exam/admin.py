from django.contrib import admin
from classmate.admin import ClassMateAdmin
from django.db import models
from django.db.models import Prefetch, Count, Q
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib import messages
from exam.forms import ExamAdminForm

from exam.models import (
    Grade, Exam, ExamResult, StudentExamSession, 
    StudentAnswer, OnlineExamResult
)


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    """Admin configuration for Grade model"""
    list_display = ('grade',)
    list_filter = ('grade',)
    search_fields = ('grade',)
    ordering = ('grade',)


class ExamResultInline(admin.TabularInline):
    """Inline admin for ExamResult in Exam admin"""
    model = ExamResult
    extra = 0
    readonly_fields = ('result_id', 'percentage', 'status', 'entered_at', 'last_modified_at')
    fields = (
        'student', 'obtained_marks', 'grade', 'is_passed', 
        'was_present', 'is_verified', 'percentage', 'status'
    )
    autocomplete_fields = ('student', 'grade')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'student__user', 'grade', 'enrollment'
        ).prefetch_related('student__user')


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    """Admin configuration for Exam model"""
    list_display = (
        'title', 'batch_info', 'exam_type', 'exam_date', 'total_marks',
        'enrolled_count', 'results_count', 'is_published', 'results_published'
    )
    list_filter = (
        'exam_type', 'is_published', 'results_published', 'is_active',
        'exam_date', 'created_at'
    )
    search_fields = (
        'title', 'batch__name', 'batch__course__name', 
        'batch__course__academy__name', 'exam_id'
    )
    readonly_fields = (
        'exam_id', 'created_by', 'created_at', 'modified_by', 'modified_at', 'is_completed', 
        'can_publish_results', 'enrolled_students_count',
        'results_submitted_count', 'pending_results_count'
    )
    autocomplete_fields = ('batch', 'published_by')
    date_hierarchy = 'exam_date'
    ordering = ('-exam_date',)
    inlines = (ExamResultInline,)
    form = ExamAdminForm
    
    fieldsets = (
        ('Basic Information', {
            'fields': ((
                'subject', 'title', 'description', 'batch', 'exam_type'
            ),)
        }),
        ('Exam Configuration', {
            'fields': ((
                'exam_date', 'duration_minutes', 'total_marks', 'pass_marks'
            ),)
        }),
        ('Status & Publishing', {
            'fields': ((
                'is_active', 'is_published', 'results_published', 
                'result_published_at', 'published_by'
            ),)
        }),
        ('Notification Tracking', {
            'fields': ((
                'sms_sent', 'sms_sent_at', 'app_notification_sent', 
                'app_notification_sent_at'
            ),),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ((
                'exam_id', 'created_by', 'created_at', 'modified_by', 'modified_at'
            ),),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ((
                'is_completed', 'can_publish_results', 'enrolled_students_count',
                'results_submitted_count', 'pending_results_count'
            ),),
            'classes': ('collapse',)
        })
    )
    
    actions = ('publish_results', 'send_notifications', 'mark_as_published')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'batch__course__academy', 'published_by'
        ).annotate(
            enrolled_count=Count('batch__students', distinct=True),
            results_count=Count('results', distinct=True)
        )
    
    def batch_info(self, obj):
        """Display batch information with course and academy"""
        return f'{obj.batch.name} - {obj.batch.course.name} ({obj.batch.course.academy.name})'
    batch_info.short_description = 'Batch Information'
    batch_info.admin_order_field = 'batch__name'
    
    def enrolled_count(self, obj):
        """Display enrolled students count"""
        return obj.enrolled_count or 0
    enrolled_count.short_description = 'Enrolled Students'
    enrolled_count.admin_order_field = 'enrolled_count'
    
    def results_count(self, obj):
        """Display results count with progress indicator"""
        total = obj.enrolled_count or 0
        submitted = obj.results_count or 0
        if total > 0:
            percentage = (submitted / total) * 100
            color = 'green' if percentage == 100 else 'orange' if percentage > 0 else 'red'
            return format_html(
                f'<span style="color: {color};">{submitted}/{total} ({percentage:.1f}%)</span>'
            )
        return '0/0'
    results_count.short_description = 'Results Progress'
    
    def publish_results(self, request, queryset):
        """Action to publish exam results"""
        published_count = 0
        for exam in queryset:
            if exam.can_publish_results:
                exam.results_published = True
                exam.result_published_at = timezone.now()
                exam.published_by = request.user
                exam.save()
                published_count += 1
        
        self.message_user(
            request,
            f'Successfully published results for {published_count} exam(s).',
            messages.SUCCESS
        )
    publish_results.short_description = 'Publish selected exam results'
    
    def send_notifications(self, request, queryset):
        """Action to send notifications for published results"""
        # This would integrate with your notification service
        self.message_user(
            request,
            'Notification sending initiated for selected exams.',
            messages.INFO
        )
    send_notifications.short_description = 'Send result notifications'
    
    def mark_as_published(self, request, queryset):
        """Action to mark exams as published"""
        updated = queryset.update(is_published=True)
        self.message_user(
            request,
            f'Successfully published {updated} exam(s).',
            messages.SUCCESS
        )
    mark_as_published.short_description = 'Mark as published'


@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    """Admin configuration for ExamResult model"""
    list_display = (
        'student', 'student_name', 'exam_title', 'obtained_marks', 'total_marks',
        'percentage', 'grade', 'status', 'is_verified', 'entered_at'
    )
    list_filter = (
        'is_passed', 'is_verified', 'was_present', 'grade',
        'exam__exam_type', 'entered_at', 'exam__batch__course'
    )
    search_fields = (
        'student__user__first_name', 'student__user__last_name',
        'student__user__username', 'student__student_id',
        'exam__title', 'result_id'
    )
    readonly_fields = (
        'result_id', 'percentage', 'status', 'entered_at', 
        'last_modified_at', 'total_marks'
    )
    autocomplete_fields = ('exam', 'student', 'grade', 'entered_by', 'verified_by')
    date_hierarchy = 'entered_at'
    ordering = ('-entered_at',)
    
    fieldsets = (
        ('Result Information', {
            'fields': (
                'exam', 'student', 'enrollment'
            )
        }),
        ('Marks & Grade', {
            'fields': (
                'obtained_marks', 'total_marks', 'grade', 'percentage',
                'is_passed', 'status'
            )
        }),
        ('Attendance & Verification', {
            'fields': (
                'was_present', 'is_verified', 'verified_by', 'verified_at'
            )
        }),
        ('Entry Tracking', {
            'fields': (
                'entered_by', 'entered_at', 'last_modified_by', 'last_modified_at'
            ),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': (
                'remarks', 'result_id'
            ),
            'classes': ('collapse',)
        })
    )
    
    actions = ('verify_results', 'mark_as_passed', 'recalculate_grades')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'exam', 'student__user', 'grade', 'entered_by', 'verified_by'
        )
    
    def student_name(self, obj):
        """Display student full name with link"""
        url = reverse('admin:student_student_change', args=[obj.student.pk])
        return format_html('<a href="{}">{}</a>', url, obj.student.user.get_full_name())
    student_name.short_description = 'Student Profile'
    student_name.admin_order_field = 'student__user__first_name'
    
    def exam_title(self, obj):
        """Display exam title with link"""
        url = reverse('admin:exam_exam_change', args=[obj.exam.pk])
        return format_html('<a href="{}">{}</a>', url, obj.exam.title)
    exam_title.short_description = 'Exam'
    exam_title.admin_order_field = 'exam__title'
    
    def total_marks(self, obj):
        """Display total marks from exam"""
        return obj.exam.total_marks
    total_marks.short_description = 'Total Marks'
    
    def verify_results(self, request, queryset):
        """Action to verify selected results"""
        updated = queryset.update(
            is_verified=True,
            verified_by=request.user,
            verified_at=timezone.now()
        )
        self.message_user(
            request,
            f'Successfully verified {updated} result(s).',
            messages.SUCCESS
        )
    verify_results.short_description = 'Verify selected results'
    
    def mark_as_passed(self, request, queryset):
        """Action to mark results as passed"""
        updated = queryset.filter(
            obtained_marks__gte=models.F('exam__pass_marks')
        ).update(is_passed=True)
        self.message_user(
            request,
            f'Successfully updated {updated} result(s).',
            messages.SUCCESS
        )
    mark_as_passed.short_description = 'Mark as passed (if eligible)'
    
    def recalculate_grades(self, request, queryset):
        """Action to recalculate grades"""
        updated_count = 0
        for result in queryset:
            try:
                result.save()  # This will trigger grade recalculation
                updated_count += 1
            except Exception as e:
                self.message_user(
                    request,
                    f'Error recalculating grade for {result}: {e}',
                    messages.ERROR
                )
        
        self.message_user(
            request,
            f'Successfully recalculated grades for {updated_count} result(s).',
            messages.SUCCESS
        )
    recalculate_grades.short_description = 'Recalculate grades'


class StudentAnswerInline(admin.TabularInline):
    """Inline admin for StudentAnswer in StudentExamSession admin"""
    model = StudentAnswer
    extra = 0
    readonly_fields = ('answered_at', 'last_modified_at', 'is_correct')
    fields = (
        'question', 'selected_option', 'text_answer', 'is_correct',
        'awarded_marks', 'is_graded'
    )
    autocomplete_fields = ('question', 'selected_option')


@admin.register(StudentExamSession)
class StudentExamSessionAdmin(admin.ModelAdmin):
    """Admin configuration for StudentExamSession model"""
    list_display = (
        'student_name', 'exam_title', 'status', 'started_at',
        'time_spent', 'remaining_time', 'ip_address'
    )
    list_filter = (
        'status', 'is_time_extended', 'started_at', 'exam__exam_type'
    )
    search_fields = (
        'student__user__first_name', 'student__user__last_name',
        'exam__title', 'session_id', 'ip_address'
    )
    readonly_fields = (
        'session_id', 'started_at', 'last_activity_at',
        'is_active', 'total_allowed_minutes', 'remaining_minutes', 'is_timeout'
    )
    autocomplete_fields = ('exam', 'student')
    date_hierarchy = 'started_at'
    ordering = ('-started_at',)
    inlines = (StudentAnswerInline,)
    
    fieldsets = (
        ('Session Information', {
            'fields': (
                'exam', 'student', 'enrollment', 'session_id'
            )
        }),
        ('Session Status', {
            'fields': (
                'status', 'started_at', 'submitted_at', 'last_activity_at'
            )
        }),
        ('Time Management', {
            'fields': (
                'time_spent_minutes', 'is_time_extended', 'extended_time_minutes',
                'total_allowed_minutes', 'remaining_minutes', 'is_timeout'
            )
        }),
        ('Technical Information', {
            'fields': (
                'ip_address', 'user_agent'
            ),
            'classes': ('collapse',)
        })
    )
    
    actions = ('extend_time', 'mark_as_submitted', 'reset_session')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'exam', 'student__user', 'enrollment'
        ).annotate(
            answer_count=Count('answers')
        )
    
    def student_name(self, obj):
        """Display student full name"""
        return obj.student.user.get_full_name()
    student_name.short_description = 'Student'
    student_name.admin_order_field = 'student__user__first_name'
    
    def exam_title(self, obj):
        """Display exam title"""
        return obj.exam.title
    exam_title.short_description = 'Exam'
    exam_title.admin_order_field = 'exam__title'
    
    def time_spent(self, obj):
        """Display time spent with formatting"""
        hours, remainder = divmod(obj.time_spent_minutes, 60)
        return f'{hours}h {remainder}m'
    time_spent.short_description = 'Time Spent'
    
    def remaining_time(self, obj):
        """Display remaining time with color coding"""
        remaining = obj.remaining_minutes
        if remaining <= 0:
            return format_html('<span style="color: red;">Time Up</span>')
        elif remaining <= 10:
            return format_html('<span style="color: orange;">{}m</span>', remaining)
        else:
            return format_html('{}m', remaining)
    remaining_time.short_description = 'Remaining Time'
    
    def extend_time(self, request, queryset):
        """Action to extend time for sessions"""
        # You might want to add a form to specify extension minutes
        extended_minutes = 30  # Default extension
        updated = queryset.filter(status='in_progress').update(
            is_time_extended=True,
            extended_time_minutes=models.F('extended_time_minutes') + extended_minutes
        )
        self.message_user(
            request,
            f'Extended time by {extended_minutes} minutes for {updated} session(s).',
            messages.SUCCESS
        )
    extend_time.short_description = f'Extend time by 30 minutes'
    
    def mark_as_submitted(self, request, queryset):
        """Action to mark sessions as submitted"""
        updated = queryset.filter(status='in_progress').update(
            status='submitted',
            submitted_at=timezone.now()
        )
        self.message_user(
            request,
            f'Marked {updated} session(s) as submitted.',
            messages.SUCCESS
        )
    mark_as_submitted.short_description = 'Mark as submitted'


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    """Admin configuration for StudentAnswer model"""
    list_display = (
        'student_name', 'exam_title', 'question_number', 'is_correct',
        'awarded_marks', 'is_graded', 'answered_at'
    )
    list_filter = (
        'is_correct', 'is_graded', 'question__question_type', 'answered_at'
    )
    search_fields = (
        'session__student__user__first_name',
        'session__student__user__last_name',
        'session__exam__title'
    )
    readonly_fields = ('answered_at', 'last_modified_at', 'is_correct')
    autocomplete_fields = ('session', 'question', 'selected_option', 'graded_by')
    date_hierarchy = 'answered_at'
    ordering = ('-answered_at',)
    
    fieldsets = (
        ('Answer Information', {
            'fields': (
                'session', 'question'
            )
        }),
        ('Answer Content', {
            'fields': (
                'selected_option', 'text_answer'
            )
        }),
        ('Scoring', {
            'fields': (
                'is_correct', 'awarded_marks', 'is_graded'
            )
        }),
        ('Manual Grading', {
            'fields': (
                'graded_by', 'graded_at', 'grader_remarks'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'answered_at', 'last_modified_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    actions = ('grade_answers', 'mark_as_correct', 'award_full_marks')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'session__student__user', 'session__exam', 'question',
            'selected_option', 'graded_by'
        )
    
    def student_name(self, obj):
        """Display student name"""
        return obj.session.student.user.get_full_name()
    student_name.short_description = 'Student'
    student_name.admin_order_field = 'session__student__user__first_name'
    
    def exam_title(self, obj):
        """Display exam title"""
        return obj.session.exam.title
    exam_title.short_description = 'Exam'
    
    def question_number(self, obj):
        """Display question number"""
        return f'Q{obj.question.question_order}'
    question_number.short_description = 'Question'
    question_number.admin_order_field = 'question__question_order'
    
    def grade_answers(self, request, queryset):
        """Action to grade ungraded answers"""
        graded_count = 0
        for answer in queryset.filter(is_graded=False):
            if answer.question.question_type in ['short_answer', 'essay']:
                # This would need manual grading interface
                pass
            else:
                answer.save()  # Auto-grade MCQ/True-False
                graded_count += 1
        
        self.message_user(
            request,
            f'Auto-graded {graded_count} answer(s).',
            messages.SUCCESS
        )
    grade_answers.short_description = 'Auto-grade selected answers'


@admin.register(OnlineExamResult)
class OnlineExamResultAdmin(ExamResultAdmin):
    """Admin configuration for OnlineExamResult model"""
    list_display = ExamResultAdmin.list_display + (
        'completion_percentage', 'auto_graded_marks', 'manual_graded_marks',
        'requires_manual_grading'
    )
    list_filter = ExamResultAdmin.list_filter + (
        'is_auto_processed', 'is_manual_grading_complete'
    )
    
    fieldsets = ExamResultAdmin.fieldsets + (
        ('Online Exam Specific', {
            'fields': (
                'session', 'auto_graded_marks', 'manual_graded_marks',
                'total_questions_attempted', 'total_questions',
                'completion_percentage'
            )
        }),
        ('Processing Status', {
            'fields': (
                'is_auto_processed', 'is_manual_grading_complete',
                'requires_manual_grading'
            ),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ExamResultAdmin.readonly_fields + (
        'completion_percentage', 'requires_manual_grading'
    )
    
    autocomplete_fields = ExamResultAdmin.autocomplete_fields + ('session',)
    
    actions = ExamResultAdmin.actions + ('process_auto_grading', 'complete_manual_grading')
    
    def process_auto_grading(self, request, queryset):
        """Action to process auto-grading"""
        processed_count = 0
        for result in queryset.filter(is_auto_processed=False):
            # Process auto-grading logic here
            result.is_auto_processed = True
            result.save()
            processed_count += 1
        
        self.message_user(
            request,
            f'Processed auto-grading for {processed_count} result(s).',
            messages.SUCCESS
        )
    process_auto_grading.short_description = 'Process auto-grading'
    
    def complete_manual_grading(self, request, queryset):
        """Action to mark manual grading as complete"""
        updated = queryset.update(is_manual_grading_complete=True)
        self.message_user(
            request,
            f'Marked manual grading complete for {updated} result(s).',
            messages.SUCCESS
        )
    complete_manual_grading.short_description = 'Mark manual grading complete'