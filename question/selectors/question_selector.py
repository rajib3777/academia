from django.db.models import QuerySet, Q, Count, Prefetch, Sum
from django.core.paginator import Paginator
from typing import Optional, Dict, Any, Tuple, List

from question.models import (
    QuestionBankCategory, 
    QuestionBank, 
    QuestionBankOption, 
    Question, 
    QuestionOption
)


class QuestionBankCategorySelector:
    """Selector for QuestionBankCategory model operations"""

    @staticmethod
    def get_by_id(category_id: int) -> Optional[QuestionBankCategory]:
        """Get category by ID with subcategories"""
        try:
            return QuestionBankCategory.objects.select_related('parent_category').prefetch_related(
                'subcategories'
            ).get(id=category_id)
        except QuestionBankCategory.DoesNotExist:
            return None

    @staticmethod
    def get_by_category_id(category_id: str) -> Optional[QuestionBankCategory]:
        """Get category by category_id"""
        try:
            return QuestionBankCategory.objects.select_related('parent_category').get(
                category_id=category_id
            )
        except QuestionBankCategory.DoesNotExist:
            return None

    @staticmethod
    def list_active_categories() -> QuerySet[QuestionBankCategory]:
        """Get all active categories with hierarchy"""
        return QuestionBankCategory.objects.filter(
            is_active=True
        ).select_related('parent_category').prefetch_related('subcategories').order_by('name')

    @staticmethod
    def list_root_categories() -> QuerySet[QuestionBankCategory]:
        """Get root categories (no parent) with their subcategories"""
        return QuestionBankCategory.objects.filter(
            is_active=True,
            parent_category__isnull=True
        ).prefetch_related('subcategories').order_by('name')

    @staticmethod
    def search_categories(search_term: str) -> QuerySet[QuestionBankCategory]:
        """Search categories by name or description"""
        return QuestionBankCategory.objects.filter(
            Q(name__icontains=search_term) | Q(description__icontains=search_term),
            is_active=True
        ).select_related('parent_category').order_by('name')

    @staticmethod
    def get_categories_with_question_count() -> QuerySet[QuestionBankCategory]:
        """Get categories annotated with question count"""
        return QuestionBankCategory.objects.filter(
            is_active=True
        ).select_related('parent_category').annotate(
            question_count=Count('questions', filter=Q(questions__is_active=True))
        ).order_by('name')


class QuestionBankSelector:
    """Selector for QuestionBank model operations"""

    @staticmethod
    def get_by_id(question_id: int) -> Optional[QuestionBank]:
        """Get question by ID with related data"""
        try:
            return QuestionBank.objects.select_related(
                'category', 'created_by', 'approved_by'
            ).prefetch_related(
                'options'
            ).get(id=question_id)
        except QuestionBank.DoesNotExist:
            return None

    @staticmethod
    def get_by_question_bank_id(question_bank_id: str) -> Optional[QuestionBank]:
        """Get question by question_bank_id"""
        try:
            return QuestionBank.objects.select_related(
                'category', 'created_by'
            ).prefetch_related('options').get(question_bank_id=question_bank_id)
        except QuestionBank.DoesNotExist:
            return None

    @staticmethod
    def list_active_questions() -> QuerySet[QuestionBank]:
        """Get all active questions"""
        return QuestionBank.objects.filter(
            is_active=True
        ).select_related('category', 'created_by').prefetch_related('options').order_by('-created_at')

    @staticmethod
    def list_approved_questions() -> QuerySet[QuestionBank]:
        """Get approved and active questions"""
        return QuestionBank.objects.filter(
            is_active=True,
            is_approved=True
        ).select_related('category', 'created_by', 'approved_by').prefetch_related(
            'options'
        ).order_by('-created_at')

    @staticmethod
    def filter_questions(
        subject: Optional[str] = None,
        question_type: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        category_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        is_approved: Optional[bool] = None,
        search_term: Optional[str] = None
    ) -> QuerySet[QuestionBank]:
        """Filter questions based on various criteria"""
        queryset = QuestionBank.objects.filter(is_active=True)

        if subject:
            queryset = queryset.filter(subject=subject)
        
        if question_type:
            queryset = queryset.filter(question_type=question_type)
        
        if difficulty_level:
            queryset = queryset.filter(difficulty_level=difficulty_level)
        
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        if is_approved is not None:
            queryset = queryset.filter(is_approved=is_approved)
        
        if tags:
            for tag in tags:
                queryset = queryset.filter(tags__icontains=tag)
        
        if search_term:
            queryset = queryset.filter(
                Q(title__icontains=search_term) |
                Q(question_text__icontains=search_term) |
                Q(tags__icontains=search_term)
            )

        return queryset.select_related('category', 'created_by').prefetch_related(
            'options'
        ).order_by('-created_at')

    @staticmethod
    def list_questions_paginated(
        page: int = 1,
        per_page: int = 10,
        subject: Optional[str] = None,
        question_type: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        category_id: Optional[int] = None,
        search_term: Optional[str] = None
    ) -> Tuple[QuerySet[QuestionBank], int, Any, Any, List]:
        """Get paginated list of questions"""
        queryset = QuestionBankSelector.filter_questions(
            subject=subject,
            question_type=question_type,
            difficulty_level=difficulty_level,
            category_id=category_id,
            search_term=search_term,
            is_approved=True
        )

        paginator = Paginator(queryset, per_page)
        page_obj = paginator.get_page(page)
        
        # Generate page range for pagination
        from exam.utils import get_page_range_with_ellipsis
        page_range = get_page_range_with_ellipsis(page_obj.number, paginator.num_pages)

        return page_obj.object_list, queryset.count(), paginator, page_obj, page_range

    @staticmethod
    def get_questions_by_subject_and_type(subject: str, question_type: str) -> QuerySet[QuestionBank]:
        """Get questions by subject and type"""
        return QuestionBank.objects.filter(
            subject=subject,
            question_type=question_type,
            is_active=True,
            is_approved=True
        ).select_related('category').prefetch_related('options').order_by('-created_at')

    @staticmethod
    def get_popular_questions(limit: int = 10) -> QuerySet[QuestionBank]:
        """Get most used questions"""
        return QuestionBank.objects.filter(
            is_active=True,
            is_approved=True
        ).select_related('category').prefetch_related('options').order_by(
            '-usage_count', '-created_at'
        )[:limit]


class QuestionSelector:
    """Selector for Question model operations"""

    @staticmethod
    def get_by_id(question_id: int) -> Optional[Question]:
        """Get question by ID with related data"""
        try:
            return Question.objects.select_related(
                'exam', 'question_bank', 'created_by'
            ).prefetch_related(
                'options__bank_option'
            ).get(id=question_id)
        except Question.DoesNotExist:
            return None

    @staticmethod
    def get_by_question_id(question_id: str) -> Optional[Question]:
        """Get question by question_id"""
        try:
            return Question.objects.select_related(
                'exam', 'question_bank'
            ).prefetch_related('options').get(question_id=question_id)
        except Question.DoesNotExist:
            return None

    @staticmethod
    def list_exam_questions(exam_id: int) -> QuerySet[Question]:
        """Get all questions for an exam"""
        return Question.objects.filter(
            exam_id=exam_id
        ).select_related('question_bank').prefetch_related(
            'options'
        ).order_by('question_order')

    @staticmethod
    def get_questions_with_options(exam_id: int) -> QuerySet[Question]:
        """Get exam questions with their options optimized"""
        return Question.objects.filter(
            exam_id=exam_id
        ).select_related('question_bank').prefetch_related(
            Prefetch(
                'options',
                queryset=QuestionOption.objects.select_related('bank_option').order_by('option_order')
            )
        ).order_by('question_order')

    @staticmethod
    def count_questions_by_type(exam_id: int) -> Dict[str, int]:
        """Count questions by type for an exam"""
        questions = Question.objects.filter(exam_id=exam_id).values('question_type')
        counts = {}
        for q in questions:
            question_type = q['question_type']
            counts[question_type] = counts.get(question_type, 0) + 1
        return counts

    @staticmethod
    def get_total_marks(exam_id: int) -> float:
        """Calculate total marks for an exam"""
        result = Question.objects.filter(exam_id=exam_id).aggregate(
            total_marks=Sum('marks')
        )
        return float(result['total_marks'] or 0)


class QuestionOptionSelector:
    """Selector for QuestionOption model operations"""

    @staticmethod
    def get_by_id(option_id: int) -> Optional[QuestionOption]:
        """Get option by ID"""
        try:
            return QuestionOption.objects.select_related(
                'question', 'bank_option'
            ).get(id=option_id)
        except QuestionOption.DoesNotExist:
            return None

    @staticmethod
    def list_question_options(question_id: int) -> QuerySet[QuestionOption]:
        """Get all options for a question"""
        return QuestionOption.objects.filter(
            question_id=question_id
        ).select_related('bank_option').order_by('option_order')

    @staticmethod
    def get_correct_options(question_id: int) -> QuerySet[QuestionOption]:
        """Get correct options for a question"""
        return QuestionOption.objects.filter(
            question_id=question_id,
            is_correct=True
        ).order_by('option_order')

    @staticmethod
    def count_options(question_id: int) -> int:
        """Count total options for a question"""
        return QuestionOption.objects.filter(question_id=question_id).count()


class QuestionBankOptionSelector:
    """Selector for QuestionBankOption model operations"""

    @staticmethod
    def get_by_id(option_id: int) -> Optional[QuestionBankOption]:
        """Get bank option by ID"""
        try:
            return QuestionBankOption.objects.select_related('question_bank').get(id=option_id)
        except QuestionBankOption.DoesNotExist:
            return None

    @staticmethod
    def list_bank_question_options(question_bank_id: int) -> QuerySet[QuestionBankOption]:
        """Get all options for a bank question"""
        return QuestionBankOption.objects.filter(
            question_bank_id=question_bank_id
        ).order_by('option_order')

    @staticmethod
    def get_correct_bank_options(question_bank_id: int) -> QuerySet[QuestionBankOption]:
        """Get correct options for a bank question"""
        return QuestionBankOption.objects.filter(
            question_bank_id=question_bank_id,
            is_correct=True
        ).order_by('option_order')