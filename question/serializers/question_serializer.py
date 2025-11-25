from rest_framework import serializers
from typing import Dict, Any, List, Optional

from question.models import (
    QuestionBankCategory, 
    QuestionBank, 
    QuestionBankOption, 
    Question, 
    QuestionOption
)
from account.serializers import UserSerializer


class QuestionBankCategoryListSerializer(serializers.Serializer):
    """Serializer for question bank category list"""
    id = serializers.IntegerField()
    category_id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    parent_category_name = serializers.CharField()
    subcategories_count = serializers.IntegerField()
    question_count = serializers.IntegerField()
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField()

    def to_representation(self, instance) -> Dict[str, Any]:
        return {
            'id': instance.id,
            'category_id': instance.category_id,
            'name': instance.name,
            'description': instance.description,
            'parent_category_name': instance.parent_category.name if instance.parent_category else None,
            'subcategories_count': getattr(instance, 'subcategories_count', instance.subcategories.count()),
            'question_count': getattr(instance, 'question_count', instance.questions.filter(is_active=True).count()),
            'is_active': instance.is_active,
            'created_at': instance.created_at,
        }


class QuestionBankCategoryDetailSerializer(serializers.Serializer):
    """Serializer for question bank category detail"""
    id = serializers.IntegerField()
    category_id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    parent_category = serializers.DictField()
    subcategories = serializers.ListField()
    question_count = serializers.IntegerField()
    is_active = serializers.BooleanField()
    created_by = serializers.DictField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    def to_representation(self, instance) -> Dict[str, Any]:
        return {
            'id': instance.id,
            'category_id': instance.category_id,
            'name': instance.name,
            'description': instance.description,
            'parent_category': {
                'id': instance.parent_category.id,
                'name': instance.parent_category.name,
                'category_id': instance.parent_category.category_id
            } if instance.parent_category else None,
            'subcategories': [
                {
                    'id': sub.id,
                    'name': sub.name,
                    'category_id': sub.category_id,
                    'question_count': sub.questions.filter(is_active=True).count()
                }
                for sub in instance.subcategories.filter(is_active=True)
            ],
            'question_count': instance.questions.filter(is_active=True).count(),
            'is_active': instance.is_active,
            'created_by': UserSerializer().to_representation(instance.created_by) if instance.created_by else None,
            'created_at': instance.created_at,
            'updated_at': instance.updated_at,
        }


class QuestionBankCategoryCreateSerializer(serializers.Serializer):
    """Serializer for creating question bank category"""
    name = serializers.CharField(max_length=100, required=True)
    description = serializers.CharField(required=False, allow_blank=True)
    parent_category_id = serializers.IntegerField(required=False, allow_null=True)


class QuestionBankOptionListSerializer(serializers.Serializer):
    """Serializer for question bank option list"""
    id = serializers.IntegerField()
    option_text = serializers.CharField()
    is_correct = serializers.BooleanField()
    option_order = serializers.IntegerField()
    option_label = serializers.CharField()
    explanation = serializers.CharField()

    def to_representation(self, instance) -> Dict[str, Any]:
        option_labels = ['A', 'B', 'C', 'D', 'E', 'F']
        label = option_labels[instance.option_order - 1] if instance.option_order <= len(option_labels) else str(instance.option_order)
        
        return {
            'id': instance.id,
            'option_text': instance.option_text,
            'is_correct': instance.is_correct,
            'option_order': instance.option_order,
            'option_label': label,
            'explanation': instance.explanation,
        }


class QuestionBankOptionCreateSerializer(serializers.Serializer):
    """Serializer for creating question bank option"""
    option_text = serializers.CharField(max_length=500, required=True)
    is_correct = serializers.BooleanField(default=False)
    option_order = serializers.IntegerField(required=True)
    explanation = serializers.CharField(required=False, allow_blank=True)


class QuestionBankListSerializer(serializers.Serializer):
    """Serializer for question bank list"""
    id = serializers.IntegerField()
    question_bank_id = serializers.CharField()
    title = serializers.CharField()
    question_text = serializers.CharField()
    question_type = serializers.CharField()
    question_type_display = serializers.CharField()
    subject = serializers.CharField()
    difficulty_level = serializers.CharField()
    difficulty_display = serializers.CharField()
    category_name = serializers.CharField()
    tags_list = serializers.ListField()
    suggested_marks = serializers.DecimalField(max_digits=5, decimal_places=2)
    usage_count = serializers.IntegerField()
    is_approved = serializers.BooleanField()
    is_active = serializers.BooleanField()
    created_by_name = serializers.CharField()
    created_at = serializers.DateTimeField()

    def to_representation(self, instance) -> Dict[str, Any]:
        return {
            'id': instance.id,
            'question_bank_id': instance.question_bank_id,
            'title': instance.title,
            'question_text': instance.question_text,
            'question_type': instance.question_type,
            'question_type_display': instance.get_question_type_display(),
            'subject': instance.subject,
            'difficulty_level': instance.difficulty_level,
            'difficulty_display': instance.get_difficulty_level_display(),
            'category_name': instance.category.name if instance.category else None,
            'tags_list': instance.tag_list,
            'suggested_marks': instance.suggested_marks,
            'usage_count': instance.usage_count,
            'is_approved': instance.is_approved,
            'is_active': instance.is_active,
            'created_by_name': instance.created_by.get_full_name() if instance.created_by else None,
            'created_at': instance.created_at,
        }


class QuestionBankDetailSerializer(serializers.Serializer):
    """Serializer for question bank detail"""
    id = serializers.IntegerField()
    question_bank_id = serializers.CharField()
    title = serializers.CharField()
    question_text = serializers.CharField()
    question_type = serializers.CharField()
    question_type_display = serializers.CharField()
    subject = serializers.CharField()
    difficulty_level = serializers.CharField()
    difficulty_display = serializers.CharField()
    category = serializers.DictField()
    tags_list = serializers.ListField()
    suggested_marks = serializers.DecimalField(max_digits=5, decimal_places=2)
    expected_answer = serializers.CharField()
    marking_scheme = serializers.CharField()
    usage_count = serializers.IntegerField()
    last_used_at = serializers.DateTimeField()
    is_approved = serializers.BooleanField()
    approved_by = serializers.DictField()
    approved_at = serializers.DateTimeField()
    is_active = serializers.BooleanField()
    created_by = serializers.DictField()
    options = serializers.ListField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    def to_representation(self, instance) -> Dict[str, Any]:
        return {
            'id': instance.id,
            'question_bank_id': instance.question_bank_id,
            'title': instance.title,
            'question_text': instance.question_text,
            'question_type': instance.question_type,
            'question_type_display': instance.get_question_type_display(),
            'subject': instance.subject,
            'difficulty_level': instance.difficulty_level,
            'difficulty_display': instance.get_difficulty_level_display(),
            'category': {
                'id': instance.category.id,
                'name': instance.category.name,
                'category_id': instance.category.category_id
            } if instance.category else None,
            'tags_list': instance.tag_list,
            'suggested_marks': instance.suggested_marks,
            'expected_answer': instance.expected_answer,
            'marking_scheme': instance.marking_scheme,
            'usage_count': instance.usage_count,
            'last_used_at': instance.last_used_at,
            'is_approved': instance.is_approved,
            'approved_by': UserSerializer().to_representation(instance.approved_by) if instance.approved_by else None,
            'approved_at': instance.approved_at,
            'is_active': instance.is_active,
            'created_by': UserSerializer().to_representation(instance.created_by) if instance.created_by else None,
            'options': [
                QuestionBankOptionListSerializer().to_representation(option)
                for option in instance.options.all().order_by('option_order')
            ],
            'created_at': instance.created_at,
            'updated_at': instance.updated_at,
        }


class QuestionBankCreateSerializer(serializers.Serializer):
    """Serializer for creating question bank"""
    title = serializers.CharField(max_length=255, required=True)
    question_text = serializers.CharField(required=True)
    question_type = serializers.ChoiceField(
        choices=['mcq', 'true_false', 'short_answer', 'essay'],
        default='mcq'
    )
    subject = serializers.CharField(max_length=50, required=True)
    difficulty_level = serializers.ChoiceField(
        choices=['easy', 'medium', 'hard'],
        default='medium'
    )
    category_id = serializers.IntegerField(required=False, allow_null=True)
    tags = serializers.CharField(max_length=500, required=False, allow_blank=True)
    suggested_marks = serializers.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    expected_answer = serializers.CharField(required=False, allow_blank=True)
    marking_scheme = serializers.CharField(required=False, allow_blank=True)
    options = serializers.ListField(
        child=QuestionBankOptionCreateSerializer(),
        required=False,
        allow_empty=True
    )


class QuestionOptionListSerializer(serializers.Serializer):
    """Serializer for question option list"""
    id = serializers.IntegerField()
    option_text = serializers.CharField()
    is_correct = serializers.BooleanField()
    option_order = serializers.IntegerField()
    option_label = serializers.CharField()
    explanation = serializers.CharField()
    is_from_bank = serializers.BooleanField()

    def to_representation(self, instance) -> Dict[str, Any]:
        option_labels = ['A', 'B', 'C', 'D', 'E', 'F']
        label = option_labels[instance.option_order - 1] if instance.option_order <= len(option_labels) else str(instance.option_order)
        
        return {
            'id': instance.id,
            'option_text': instance.option_text,
            'is_correct': instance.is_correct,
            'option_order': instance.option_order,
            'option_label': label,
            'explanation': instance.explanation,
            'is_from_bank': instance.bank_option is not None,
        }


class QuestionOptionCreateSerializer(serializers.Serializer):
    """Serializer for creating question option"""
    option_text = serializers.CharField(max_length=500, required=True)
    is_correct = serializers.BooleanField(default=False)
    option_order = serializers.IntegerField(required=True)
    explanation = serializers.CharField(required=False, allow_blank=True)


class QuestionListSerializer(serializers.Serializer):
    """Serializer for question list"""
    id = serializers.IntegerField()
    question_id = serializers.CharField()
    question_text = serializers.CharField()
    question_type = serializers.CharField()
    question_type_display = serializers.CharField()
    marks = serializers.DecimalField(max_digits=5, decimal_places=2)
    question_order = serializers.IntegerField()
    is_required = serializers.BooleanField()
    is_from_bank = serializers.BooleanField()
    bank_question_title = serializers.CharField()
    created_by_name = serializers.CharField()
    created_at = serializers.DateTimeField()

    def to_representation(self, instance) -> Dict[str, Any]:
        return {
            'id': instance.id,
            'question_id': instance.question_id,
            'question_text': instance.question_text,
            'question_type': instance.question_type,
            'question_type_display': instance.get_question_type_display(),
            'marks': instance.marks,
            'question_order': instance.question_order,
            'is_required': instance.is_required,
            'is_from_bank': instance.is_from_bank,
            'bank_question_title': instance.question_bank.title if instance.question_bank else None,
            'created_by_name': instance.created_by.get_full_name() if instance.created_by else None,
            'created_at': instance.created_at,
        }


class QuestionDetailSerializer(serializers.Serializer):
    """Serializer for question detail"""
    id = serializers.IntegerField()
    question_id = serializers.CharField()
    question_text = serializers.CharField()
    question_type = serializers.CharField()
    question_type_display = serializers.CharField()
    marks = serializers.DecimalField(max_digits=5, decimal_places=2)
    question_order = serializers.IntegerField()
    is_required = serializers.BooleanField()
    expected_answer = serializers.CharField()
    marking_scheme = serializers.CharField()
    is_from_bank = serializers.BooleanField()
    question_bank = serializers.DictField()
    exam = serializers.DictField()
    created_by = serializers.DictField()
    options = serializers.ListField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    def to_representation(self, instance) -> Dict[str, Any]:
        return {
            'id': instance.id,
            'question_id': instance.question_id,
            'question_text': instance.question_text,
            'question_type': instance.question_type,
            'question_type_display': instance.get_question_type_display(),
            'marks': instance.marks,
            'question_order': instance.question_order,
            'is_required': instance.is_required,
            'expected_answer': instance.expected_answer,
            'marking_scheme': instance.marking_scheme,
            'is_from_bank': instance.is_from_bank,
            'question_bank': {
                'id': instance.question_bank.id,
                'title': instance.question_bank.title,
                'question_bank_id': instance.question_bank.question_bank_id,
                'subject': instance.question_bank.subject,
                'difficulty_level': instance.question_bank.difficulty_level
            } if instance.question_bank else None,
            'exam': {
                'id': instance.exam.id,
                'title': instance.exam.title,
                'exam_code': instance.exam.exam_code
            } if instance.exam else None,
            'created_by': UserSerializer().to_representation(instance.created_by) if instance.created_by else None,
            'options': [
                QuestionOptionListSerializer().to_representation(option)
                for option in instance.options.all().order_by('option_order')
            ],
            'created_at': instance.created_at,
            'updated_at': instance.updated_at,
        }


class QuestionCreateFromBankSerializer(serializers.Serializer):
    """Serializer for creating question from bank"""
    question_bank_id = serializers.CharField(required=True)
    marks = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    question_order = serializers.IntegerField(required=False)
    is_required = serializers.BooleanField(default=True)


class QuestionCreateCustomSerializer(serializers.Serializer):
    """Serializer for creating custom question"""
    question_text = serializers.CharField(required=True)
    question_type = serializers.ChoiceField(
        choices=['mcq', 'true_false', 'short_answer', 'essay'],
        default='mcq'
    )
    marks = serializers.DecimalField(max_digits=5, decimal_places=2, required=True)
    question_order = serializers.IntegerField(required=False)
    is_required = serializers.BooleanField(default=True)
    expected_answer = serializers.CharField(required=False, allow_blank=True)
    marking_scheme = serializers.CharField(required=False, allow_blank=True)
    options = serializers.ListField(
        child=QuestionOptionCreateSerializer(),
        required=False,
        allow_empty=True
    )


class QuestionUpdateSerializer(serializers.Serializer):
    """Serializer for updating question"""
    question_text = serializers.CharField(required=False)
    marks = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    question_order = serializers.IntegerField(required=False)
    is_required = serializers.BooleanField(required=False)
    expected_answer = serializers.CharField(required=False, allow_blank=True)
    marking_scheme = serializers.CharField(required=False, allow_blank=True)


class QuestionReorderSerializer(serializers.Serializer):
    """Serializer for reordering questions"""
    questions = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField()
        ),
        required=True
    )