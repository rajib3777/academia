from django.contrib import admin
from django.db.models import Prefetch, Count, Q, F
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.forms import ModelForm
from django.db import transaction

from question.models import (
    QuestionBankCategory, QuestionBank, QuestionBankOption,
    Question, QuestionOption
)


class QuestionBankOptionInline(admin.TabularInline):
    """Inline admin for QuestionBankOption in QuestionBank admin"""
    model = QuestionBankOption
    extra = 1
    readonly_fields = ('created_at', 'modified_at')
    fields = ('option_text', 'is_correct', 'option_order', 'explanation')
    ordering = ('option_order',)

    def get_queryset(self, request):
        return super().get_queryset(request).order_by('option_order')


@admin.register(QuestionBankCategory)
class QuestionBankCategoryAdmin(admin.ModelAdmin):
    """Admin configuration for QuestionBankCategory model"""
    list_display = (
        'name', 'parent_category', 'question_count',
        'is_active', 'created_by', 'created_at'
    )
    list_filter = (
        'is_active','parent_category', 'created_at'
    )
    search_fields = (
        'name', 'description', 
        'category_id'
    )
    readonly_fields = (
        'category_id', 'created_at', 'modified_at'
    )
    autocomplete_fields = ('parent_category', 'created_by')
    date_hierarchy = 'created_at'
    ordering = ('name', )

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'subject')
        }),
        ('Hierarchy', {
            'fields': ('parent_category',)
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
        ('System Information', {
            'fields': ('category_id', 'created_by', 'created_at', 'modified_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ('mark_as_active', 'mark_as_inactive', 'move_to_category')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'parent_category', 'created_by'
        ).annotate(
            question_count=Count('questions', distinct=True)
        )

    def question_count(self, obj):
        """Display question count in this category"""
        count = obj.question_count or 0
        if count > 0:
            url = reverse('admin:question_questionbank_changelist')
            return format_html(
                '<a href="{}?category__id__exact={}">{}</a>',
                url, obj.pk, count
            )
        return count
    question_count.short_description = 'Questions'
    question_count.admin_order_field = 'question_count'
    
    def mark_as_active(self, request, queryset):
        """Action to mark categories as active"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'Marked {updated} category(ies) as active.',
            messages.SUCCESS
        )
    mark_as_active.short_description = 'Mark as active'
    
    def mark_as_inactive(self, request, queryset):
        """Action to mark categories as inactive"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'Marked {updated} category(ies) as inactive.',
            messages.SUCCESS
        )
    mark_as_inactive.short_description = 'Mark as inactive'


@admin.register(QuestionBank)
class QuestionBankAdmin(admin.ModelAdmin):
    """Admin configuration for QuestionBank model"""
    list_display = (
        'title', 'question_type', 'subject', 'category', 'difficulty_level',
        'suggested_marks', 'usage_count', 'is_approved', 'is_active'
    )
    list_filter = (
        'question_type', 'difficulty_level', 'is_approved', 'is_active',
        'subject', 'category', 'created_at', 'last_used_at'
    )
    search_fields = (
        'title', 'question_text', 'tags', 'subject',
        'category__name', 'question_bank_id'
    )
    readonly_fields = (
        'question_bank_id', 'usage_count', 'last_used_at',
        'tag_list', 'is_mcq_or_true_false', 'created_at', 'modified_at'
    )
    autocomplete_fields = (
        'category', 'created_by', 'approved_by'
    )
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    inlines = (QuestionBankOptionInline,)
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'title', 'question_text', 'question_type', 'suggested_marks'
            )
        }),
        ('Categorization', {
            'fields': (
                'subject', 'category', 'difficulty_level', 'tags'
            )
        }),
        ('Answer Guidelines', {
            'fields': (
                'expected_answer', 'marking_scheme'
            ),
            'classes': ('collapse',)
        }),
        ('Quality Control', {
            'fields': (
                'is_approved', 'approved_by', 'approved_at', 'is_active'
            )
        }),
        ('Usage Statistics', {
            'fields': (
                'usage_count', 'last_used_at'
            ),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': (
                'question_bank_id', 'created_by', 'created_at', 'modified_at',
                'tag_list', 'is_mcq_or_true_false'
            ),
            'classes': ('collapse',)
        })
    )
    
    actions = (
        'approve_questions', 'disapprove_questions', 'mark_as_active',
        'mark_as_inactive', 'duplicate_questions'
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'category', 'created_by', 'approved_by'
        ).prefetch_related(
            Prefetch('options', queryset=QuestionBankOption.objects.order_by('option_order'))
        )

    def approve_questions(self, request, queryset):
        """Action to approve selected questions"""
        with transaction.atomic():
            updated = queryset.filter(is_approved=False).update(
                is_approved=True,
                approved_by=request.user,
                approved_at=timezone.now()
            )
        self.message_user(
            request,
            f'Approved {updated} question(s).',
            messages.SUCCESS
        )
    approve_questions.short_description = 'Approve selected questions'
    
    def disapprove_questions(self, request, queryset):
        """Action to disapprove selected questions"""
        updated = queryset.update(
            is_approved=False,
            approved_by=None,
            approved_at=None
        )
        self.message_user(
            request,
            f'Disapproved {updated} question(s).',
            messages.SUCCESS
        )
    disapprove_questions.short_description = 'Disapprove selected questions'
    
    def mark_as_active(self, request, queryset):
        """Action to mark questions as active"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'Marked {updated} question(s) as active.',
            messages.SUCCESS
        )
    mark_as_active.short_description = 'Mark as active'
    
    def mark_as_inactive(self, request, queryset):
        """Action to mark questions as inactive"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'Marked {updated} question(s) as inactive.',
            messages.SUCCESS
        )
    mark_as_inactive.short_description = 'Mark as inactive'
    
    def duplicate_questions(self, request, queryset):
        """Action to duplicate selected questions"""
        duplicated_count = 0
        with transaction.atomic():
            for question in queryset:
                # Create duplicate
                question.pk = None
                question.title = f'{question.title} (Copy)'
                question.question_bank_id = None
                question.is_approved = False
                question.approved_by = None
                question.approved_at = None
                question.usage_count = 0
                question.last_used_at = None
                question.created_by = request.user
                question.save()
                
                # Duplicate options if any
                for option in question.options.all():
                    option.pk = None
                    option.question_bank = question
                    option.save()
                
                duplicated_count += 1
        
        self.message_user(
            request,
            f'Successfully duplicated {duplicated_count} question(s).',
            messages.SUCCESS
        )
    duplicate_questions.short_description = 'Duplicate selected questions'


@admin.register(QuestionBankOption)
class QuestionBankOptionAdmin(admin.ModelAdmin):
    """Admin configuration for QuestionBankOption model"""
    list_display = (
        'question_bank', 'option_label', 'option_text_short',
        'is_correct', 'option_order'
    )
    list_filter = (
        'is_correct', 'question_bank__question_type',
        'question_bank__subject', 'question_bank__difficulty_level'
    )
    search_fields = (
        'option_text', 'explanation', 'question_bank__title',
        'question_bank__question_text'
    )
    readonly_fields = ('created_at', 'modified_at')
    autocomplete_fields = ('question_bank',)
    ordering = ('question_bank', 'option_order')
    
    fieldsets = (
        ('Option Information', {
            'fields': ('question_bank', 'option_text', 'option_order')
        }),
        ('Answer Details', {
            'fields': ('is_correct', 'explanation')
        }),
        ('System Information', {
            'fields': ('created_at', 'modified_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ('mark_as_correct', 'mark_as_incorrect')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'question_bank__category'
        )
    
    def option_label(self, obj):
        """Display option label (A, B, C, D)"""
        option_labels = ['A', 'B', 'C', 'D', 'E', 'F']
        label = option_labels[obj.option_order - 1] if obj.option_order <= len(option_labels) else str(obj.option_order)
        color = 'green' if obj.is_correct else 'black'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, label
        )
    option_label.short_description = 'Label'
    option_label.admin_order_field = 'option_order'
    
    def option_text_short(self, obj):
        """Display shortened option text"""
        return obj.option_text[:50] + '...' if len(obj.option_text) > 50 else obj.option_text
    option_text_short.short_description = 'Option Text'
    
    def mark_as_correct(self, request, queryset):
        """Action to mark options as correct"""
        updated = queryset.update(is_correct=True)
        self.message_user(
            request,
            f'Marked {updated} option(s) as correct.',
            messages.SUCCESS
        )
    mark_as_correct.short_description = 'Mark as correct'
    
    def mark_as_incorrect(self, request, queryset):
        """Action to mark options as incorrect"""
        updated = queryset.update(is_correct=False)
        self.message_user(
            request,
            f'Marked {updated} option(s) as incorrect.',
            messages.SUCCESS
        )
    mark_as_incorrect.short_description = 'Mark as incorrect'


class QuestionOptionInline(admin.TabularInline):
    """Inline admin for QuestionOption in Question admin"""
    model = QuestionOption
    extra = 1
    readonly_fields = ('created_at', 'modified_at')
    fields = ('option_text', 'is_correct', 'option_order', 'explanation', 'bank_option')
    autocomplete_fields = ('bank_option',)
    ordering = ('option_order',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('bank_option').order_by('option_order')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Admin configuration for Question model"""
    list_display = (
        'question_order', 'exam_title', 'question_type', 'marks',
        'is_from_bank', 'is_required', 'created_by'
    )
    list_filter = (
        'question_type', 'is_required', 'exam__exam_type',
        'exam__batch__course', 'created_at'
    )
    search_fields = (
        'question_text', 'exam__title', 'exam__batch__name',
        'question_id', 'question_bank__title'
    )
    readonly_fields = (
        'question_id', 'is_from_bank', 'created_at', 'modified_at'
    )
    autocomplete_fields = ('exam', 'question_bank', 'created_by')
    date_hierarchy = 'created_at'
    ordering = ('exam', 'question_order')
    inlines = (QuestionOptionInline,)
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'exam', 'question_order', 'question_type', 'marks', 'is_required'
            )
        }),
        ('Question Content', {
            'fields': (
                'question_text', 'expected_answer', 'marking_scheme'
            )
        }),
        ('Question Bank Reference', {
            'fields': (
                'question_bank', 'is_from_bank'
            ),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': (
                'question_id', 'created_by', 'created_at', 'modified_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    actions = ('copy_from_bank', 'mark_as_required', 'mark_as_optional', 'reorder_questions')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'exam__batch__course', 'question_bank', 'created_by'
        ).prefetch_related(
            Prefetch('options', queryset=QuestionOption.objects.order_by('option_order'))
        )
    
    def exam_title(self, obj):
        """Display exam title with link"""
        url = reverse('admin:exam_exam_change', args=[obj.exam.pk])
        return format_html('<a href="{}">{}</a>', url, obj.exam.title)
    exam_title.short_description = 'Exam'
    exam_title.admin_order_field = 'exam__title'
    
    def copy_from_bank(self, request, queryset):
        """Action to copy question content from question bank"""
        updated_count = 0
        for question in queryset.filter(question_bank__isnull=False):
            if question.question_bank:
                question.question_text = question.question_bank.question_text
                question.question_type = question.question_bank.question_type
                question.expected_answer = question.question_bank.expected_answer
                question.marking_scheme = question.question_bank.marking_scheme
                question.save()
                updated_count += 1
        
        self.message_user(
            request,
            f'Updated {updated_count} question(s) from question bank.',
            messages.SUCCESS
        )
    copy_from_bank.short_description = 'Copy content from question bank'
    
    def mark_as_required(self, request, queryset):
        """Action to mark questions as required"""
        updated = queryset.update(is_required=True)
        self.message_user(
            request,
            f'Marked {updated} question(s) as required.',
            messages.SUCCESS
        )
    mark_as_required.short_description = 'Mark as required'
    
    def mark_as_optional(self, request, queryset):
        """Action to mark questions as optional"""
        updated = queryset.update(is_required=False)
        self.message_user(
            request,
            f'Marked {updated} question(s) as optional.',
            messages.SUCCESS
        )
    mark_as_optional.short_description = 'Mark as optional'


@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    """Admin configuration for QuestionOption model"""
    list_display = (
        'question_info', 'option_label', 'option_text_short',
        'is_correct', 'option_order', 'from_bank'
    )
    list_filter = (
        'is_correct', 'question__question_type',
        'question__exam__batch__course', 'created_at'
    )
    search_fields = (
        'option_text', 'explanation', 'question__question_text',
        'question__exam__title'
    )
    readonly_fields = ('created_at', 'modified_at')
    autocomplete_fields = ('question', 'bank_option')
    ordering = ('question', 'option_order')
    
    fieldsets = (
        ('Option Information', {
            'fields': ('question', 'option_text', 'option_order')
        }),
        ('Answer Details', {
            'fields': ('is_correct', 'explanation')
        }),
        ('Bank Reference', {
            'fields': ('bank_option',),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_at', 'modified_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ('mark_as_correct', 'mark_as_incorrect', 'copy_from_bank')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'question__exam', 'bank_option'
        )
    
    def question_info(self, obj):
        """Display question information"""
        return f'Q{obj.question.question_order} - {obj.question.exam.title}'
    question_info.short_description = 'Question'
    question_info.admin_order_field = 'question__question_order'
    
    def option_label(self, obj):
        """Display option label (A, B, C, D)"""
        option_labels = ['A', 'B', 'C', 'D', 'E', 'F']
        label = option_labels[obj.option_order - 1] if obj.option_order <= len(option_labels) else str(obj.option_order)
        color = 'green' if obj.is_correct else 'black'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, label
        )
    option_label.short_description = 'Label'
    option_label.admin_order_field = 'option_order'
    
    def option_text_short(self, obj):
        """Display shortened option text"""
        return obj.option_text[:50] + '...' if len(obj.option_text) > 50 else obj.option_text
    option_text_short.short_description = 'Option Text'
    
    def from_bank(self, obj):
        """Show if option is from question bank"""
        if obj.bank_option:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    from_bank.short_description = 'From Bank'
    from_bank.boolean = True
    
    def mark_as_correct(self, request, queryset):
        """Action to mark options as correct"""
        updated = queryset.update(is_correct=True)
        self.message_user(
            request,
            f'Marked {updated} option(s) as correct.',
            messages.SUCCESS
        )
    mark_as_correct.short_description = 'Mark as correct'
    
    def mark_as_incorrect(self, request, queryset):
        """Action to mark options as incorrect"""
        updated = queryset.update(is_correct=False)
        self.message_user(
            request,
            f'Marked {updated} option(s) as incorrect.',
            messages.SUCCESS
        )
    mark_as_incorrect.short_description = 'Mark as incorrect'
    
    def copy_from_bank(self, request, queryset):
        """Action to copy option content from bank"""
        updated_count = 0
        for option in queryset.filter(bank_option__isnull=False):
            if option.bank_option:
                option.option_text = option.bank_option.option_text
                option.is_correct = option.bank_option.is_correct
                option.explanation = option.bank_option.explanation
                option.save()
                updated_count += 1
        
        self.message_user(
            request,
            f'Updated {updated_count} option(s) from question bank.',
            messages.SUCCESS
        )
    copy_from_bank.short_description = 'Copy content from bank'

