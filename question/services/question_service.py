from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Dict, Any, List, Optional

from question.models import (
    QuestionBankCategory, 
    QuestionBank, 
    QuestionBankOption, 
    Question, 
    QuestionOption
)
from question.selectors.question_selector import (
    QuestionBankCategorySelector,
    QuestionBankSelector,
    QuestionSelector,
    QuestionOptionSelector,
    QuestionBankOptionSelector
)
from account.models import User


class QuestionBankCategoryService:
    """Service for QuestionBankCategory operations"""

    @staticmethod
    @transaction.atomic
    def create_category(
        name: str,
        description: str = "",
        parent_category_id: Optional[int] = None,
        created_by: Optional[User] = None
    ) -> QuestionBankCategory:
        """Create a new question bank category"""
        
        # Check if category with same name exists
        if QuestionBankCategory.objects.filter(name=name).exists():
            raise ValidationError(f"Category with name '{name}' already exists")
        
        # Validate parent category if provided
        parent_category = None
        if parent_category_id:
            parent_category = QuestionBankCategorySelector.get_by_id(parent_category_id)
            if not parent_category:
                raise ValidationError("Parent category not found")
            if not parent_category.is_active:
                raise ValidationError("Parent category is not active")

        category = QuestionBankCategory.objects.create(
            name=name,
            description=description,
            parent_category=parent_category,
            created_by=created_by,
            is_active=True
        )
        
        return category

    @staticmethod
    @transaction.atomic
    def update_category(
        category_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        parent_category_id: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> QuestionBankCategory:
        """Update an existing category"""
        
        category = QuestionBankCategorySelector.get_by_id(category_id)
        if not category:
            raise ValidationError("Category not found")

        # Check for name uniqueness if name is being changed
        if name and name != category.name:
            if QuestionBankCategory.objects.filter(name=name).exists():
                raise ValidationError(f"Category with name '{name}' already exists")
            category.name = name

        if description is not None:
            category.description = description

        # Handle parent category change
        if parent_category_id is not None:
            if parent_category_id == category.id:
                raise ValidationError("Category cannot be its own parent")
            
            parent_category = None
            if parent_category_id:
                parent_category = QuestionBankCategorySelector.get_by_id(parent_category_id)
                if not parent_category:
                    raise ValidationError("Parent category not found")
                if not parent_category.is_active:
                    raise ValidationError("Parent category is not active")
            
            category.parent_category = parent_category

        if is_active is not None:
            category.is_active = is_active

        category.save()
        return category

    @staticmethod
    @transaction.atomic
    def delete_category(category_id: int) -> bool:
        """Soft delete a category (deactivate)"""
        
        category = QuestionBankCategorySelector.get_by_id(category_id)
        if not category:
            raise ValidationError("Category not found")

        # Check if category has active subcategories
        if category.subcategories.filter(is_active=True).exists():
            raise ValidationError("Cannot delete category with active subcategories")

        # Check if category has questions
        if category.questions.filter(is_active=True).exists():
            raise ValidationError("Cannot delete category with active questions")

        category.is_active = False
        category.save()
        return True


class QuestionBankService:
    """Service for QuestionBank operations"""

    @staticmethod
    @transaction.atomic
    def create_question(
        title: str,
        question_text: str,
        question_type: str,
        subject: str,
        difficulty_level: str = 'medium',
        category_id: Optional[int] = None,
        tags: str = "",
        suggested_marks: float = 1.0,
        expected_answer: str = "",
        marking_scheme: str = "",
        created_by: Optional[User] = None,
        options_data: Optional[List[Dict[str, Any]]] = None
    ) -> QuestionBank:
        """Create a new question in the question bank"""

        # Validate category if provided
        category = None
        if category_id:
            category = QuestionBankCategorySelector.get_by_id(category_id)
            if not category or not category.is_active:
                raise ValidationError("Invalid or inactive category")

        # Create the question
        question = QuestionBank.objects.create(
            title=title,
            question_text=question_text,
            question_type=question_type,
            subject=subject,
            difficulty_level=difficulty_level,
            category=category,
            tags=tags,
            suggested_marks=suggested_marks,
            expected_answer=expected_answer,
            marking_scheme=marking_scheme,
            created_by=created_by,
            is_active=True,
            is_approved=False
        )

        # Create options for MCQ and True/False questions
        if question_type in ['mcq', 'true_false'] and options_data:
            QuestionBankOptionService.create_options_for_question(question.id, options_data)

        return question

    @staticmethod
    @transaction.atomic
    def update_question(
        question_id: int,
        title: Optional[str] = None,
        question_text: Optional[str] = None,
        question_type: Optional[str] = None,
        subject: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        category_id: Optional[int] = None,
        tags: Optional[str] = None,
        suggested_marks: Optional[float] = None,
        expected_answer: Optional[str] = None,
        marking_scheme: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> QuestionBank:
        """Update an existing question"""

        question = QuestionBankSelector.get_by_id(question_id)
        if not question:
            raise ValidationError("Question not found")

        # Update fields if provided
        if title is not None:
            question.title = title
        if question_text is not None:
            question.question_text = question_text
        if question_type is not None:
            question.question_type = question_type
        if subject is not None:
            question.subject = subject
        if difficulty_level is not None:
            question.difficulty_level = difficulty_level
        if tags is not None:
            question.tags = tags
        if suggested_marks is not None:
            question.suggested_marks = suggested_marks
        if expected_answer is not None:
            question.expected_answer = expected_answer
        if marking_scheme is not None:
            question.marking_scheme = marking_scheme
        if is_active is not None:
            question.is_active = is_active

        # Handle category change
        if category_id is not None:
            category = None
            if category_id:
                category = QuestionBankCategorySelector.get_by_id(category_id)
                if not category or not category.is_active:
                    raise ValidationError("Invalid or inactive category")
            question.category = category

        question.save()
        return question

    @staticmethod
    @transaction.atomic
    def approve_question(question_id: int, approved_by: User) -> QuestionBank:
        """Approve a question for use"""

        question = QuestionBankSelector.get_by_id(question_id)
        if not question:
            raise ValidationError("Question not found")

        if question.is_approved:
            raise ValidationError("Question is already approved")

        question.is_approved = True
        question.approved_by = approved_by
        question.approved_at = timezone.now()
        question.save()

        return question

    @staticmethod
    @transaction.atomic
    def unapprove_question(question_id: int) -> QuestionBank:
        """Remove approval from a question"""

        question = QuestionBankSelector.get_by_id(question_id)
        if not question:
            raise ValidationError("Question not found")

        question.is_approved = False
        question.approved_by = None
        question.approved_at = None
        question.save()

        return question

    @staticmethod
    @transaction.atomic
    def delete_question(question_id: int) -> bool:
        """Soft delete a question (deactivate)"""

        question = QuestionBankSelector.get_by_id(question_id)
        if not question:
            raise ValidationError("Question not found")

        # Check if question is being used in active exams
        if question.exam_questions.filter(exam__is_active=True).exists():
            raise ValidationError("Cannot delete question that is being used in active exams")

        question.is_active = False
        question.save()
        return True

    @staticmethod
    @transaction.atomic
    def duplicate_question(question_id: int, created_by: Optional[User] = None) -> QuestionBank:
        """Create a duplicate of an existing question"""

        original_question = QuestionBankSelector.get_by_id(question_id)
        if not original_question:
            raise ValidationError("Question not found")

        # Create duplicate question
        duplicate_question = QuestionBank.objects.create(
            title=f"{original_question.title} (Copy)",
            question_text=original_question.question_text,
            question_type=original_question.question_type,
            subject=original_question.subject,
            category=original_question.category,
            difficulty_level=original_question.difficulty_level,
            tags=original_question.tags,
            suggested_marks=original_question.suggested_marks,
            expected_answer=original_question.expected_answer,
            marking_scheme=original_question.marking_scheme,
            created_by=created_by,
            is_active=True,
            is_approved=False
        )

        # Duplicate options if they exist
        original_options = QuestionBankOptionSelector.list_bank_question_options(original_question.id)
        for option in original_options:
            QuestionBankOption.objects.create(
                question_bank=duplicate_question,
                option_text=option.option_text,
                is_correct=option.is_correct,
                option_order=option.option_order,
                explanation=option.explanation
            )

        return duplicate_question


class QuestionBankOptionService:
    """Service for QuestionBankOption operations"""

    @staticmethod
    @transaction.atomic
    def create_option(
        question_bank_id: int,
        option_text: str,
        is_correct: bool = False,
        option_order: int = 1,
        explanation: str = ""
    ) -> QuestionBankOption:
        """Create a new option for a question bank question"""

        question_bank = QuestionBankSelector.get_by_id(question_bank_id)
        if not question_bank:
            raise ValidationError("Question not found")

        if not question_bank.is_mcq_or_true_false:
            raise ValidationError("Options can only be added to MCQ or True/False questions")

        # Check if option order already exists
        if QuestionBankOption.objects.filter(
            question_bank_id=question_bank_id, 
            option_order=option_order
        ).exists():
            raise ValidationError(f"Option with order {option_order} already exists")

        option = QuestionBankOption.objects.create(
            question_bank=question_bank,
            option_text=option_text,
            is_correct=is_correct,
            option_order=option_order,
            explanation=explanation
        )

        return option

    @staticmethod
    @transaction.atomic
    def create_options_for_question(
        question_bank_id: int, 
        options_data: List[Dict[str, Any]]
    ) -> List[QuestionBankOption]:
        """Create multiple options for a question"""

        question_bank = QuestionBankSelector.get_by_id(question_bank_id)
        if not question_bank:
            raise ValidationError("Question not found")

        if not question_bank.is_mcq_or_true_false:
            raise ValidationError("Options can only be added to MCQ or True/False questions")

        # Delete existing options
        QuestionBankOption.objects.filter(question_bank_id=question_bank_id).delete()

        options = []
        for option_data in options_data:
            option = QuestionBankOption.objects.create(
                question_bank=question_bank,
                option_text=option_data.get('option_text', ''),
                is_correct=option_data.get('is_correct', False),
                option_order=option_data.get('option_order', len(options) + 1),
                explanation=option_data.get('explanation', '')
            )
            options.append(option)

        return options

    @staticmethod
    @transaction.atomic
    def update_option(
        option_id: int,
        option_text: Optional[str] = None,
        is_correct: Optional[bool] = None,
        explanation: Optional[str] = None
    ) -> QuestionBankOption:
        """Update an existing option"""

        option = QuestionBankOptionSelector.get_by_id(option_id)
        if not option:
            raise ValidationError("Option not found")

        if option_text is not None:
            option.option_text = option_text
        if is_correct is not None:
            option.is_correct = is_correct
        if explanation is not None:
            option.explanation = explanation

        option.save()
        return option

    @staticmethod
    @transaction.atomic
    def delete_option(option_id: int) -> bool:
        """Delete an option"""

        option = QuestionBankOptionSelector.get_by_id(option_id)
        if not option:
            raise ValidationError("Option not found")

        option.delete()
        return True


class QuestionService:
    """Service for Question operations"""

    @staticmethod
    @transaction.atomic
    def create_question_from_bank(
        exam_id: int,
        question_bank_id: int,
        marks: Optional[float] = None,
        question_order: Optional[int] = None,
        is_required: bool = True
    ) -> Question:
        """Create exam question from question bank"""

        question_bank = QuestionBankSelector.get_by_question_bank_id(question_bank_id)
        if not question_bank:
            raise ValidationError("Question bank question not found")

        if not question_bank.is_approved or not question_bank.is_active:
            raise ValidationError("Question bank question must be approved and active")

        # Auto-generate question order if not provided
        if question_order is None:
            last_question = Question.objects.filter(exam_id=exam_id).order_by('-question_order').first()
            question_order = (last_question.question_order + 1) if last_question else 1

        # Use suggested marks if not provided
        if marks is None:
            marks = question_bank.suggested_marks

        question = Question.objects.create(
            exam_id=exam_id,
            question_bank=question_bank,
            question_text=question_bank.question_text,
            question_type=question_bank.question_type,
            marks=marks,
            question_order=question_order,
            is_required=is_required,
            expected_answer=question_bank.expected_answer,
            marking_scheme=question_bank.marking_scheme
        )

        # Create options from bank options
        bank_options = QuestionBankOptionSelector.list_bank_question_options(question_bank.id)
        for bank_option in bank_options:
            QuestionOption.objects.create(
                question=question,
                bank_option=bank_option,
                option_text=bank_option.option_text,
                is_correct=bank_option.is_correct,
                option_order=bank_option.option_order,
                explanation=bank_option.explanation
            )

        return question

    @staticmethod
    @transaction.atomic
    def create_custom_question(
        exam_id: int,
        question_text: str,
        question_type: str,
        marks: float,
        question_order: Optional[int] = None,
        is_required: bool = True,
        expected_answer: str = "",
        marking_scheme: str = "",
        created_by: Optional[User] = None,
        options_data: Optional[List[Dict[str, Any]]] = None
    ) -> Question:
        """Create custom exam question (not from question bank)"""

        # Auto-generate question order if not provided
        if question_order is None:
            last_question = Question.objects.filter(exam_id=exam_id).order_by('-question_order').first()
            question_order = (last_question.question_order + 1) if last_question else 1

        question = Question.objects.create(
            exam_id=exam_id,
            question_text=question_text,
            question_type=question_type,
            marks=marks,
            question_order=question_order,
            is_required=is_required,
            expected_answer=expected_answer,
            marking_scheme=marking_scheme,
            created_by=created_by
        )

        # Create options for MCQ and True/False questions
        if question_type in ['mcq', 'true_false'] and options_data:
            QuestionOptionService.create_options_for_question(question.id, options_data)

        return question

    @staticmethod
    @transaction.atomic
    def update_question(
        question_id: int,
        question_text: Optional[str] = None,
        marks: Optional[float] = None,
        question_order: Optional[int] = None,
        is_required: Optional[bool] = None,
        expected_answer: Optional[str] = None,
        marking_scheme: Optional[str] = None
    ) -> Question:
        """Update an existing exam question"""

        question = QuestionSelector.get_by_id(question_id)
        if not question:
            raise ValidationError("Question not found")

        if question_text is not None:
            question.question_text = question_text
        if marks is not None:
            question.marks = marks
        if question_order is not None:
            # Check for duplicate order in same exam
            existing = Question.objects.filter(
                exam=question.exam,
                question_order=question_order
            ).exclude(id=question.id).exists()
            if existing:
                raise ValidationError(f"Question with order {question_order} already exists in this exam")
            question.question_order = question_order
        if is_required is not None:
            question.is_required = is_required
        if expected_answer is not None:
            question.expected_answer = expected_answer
        if marking_scheme is not None:
            question.marking_scheme = marking_scheme

        question.save()
        return question

    @staticmethod
    @transaction.atomic
    def create_question(
        exam,
        question_text: str,
        question_type: str,
        marks: float,
        question_order: int,
        is_required: bool,
        expected_answer: str,
        marking_scheme: str,
        created_by: User,
        options: List[Dict[str, Any]],
        category: Optional[QuestionBankCategory] = None,
        subject: Optional[str] = None,
        difficulty_level: Optional[str] = 'medium',
        tags: Optional[str] = '',
    ) -> Question:
        # Create QuestionBank entry
        bank = QuestionBank.objects.create(
            title=question_text[:50],
            question_text=question_text,
            question_type=question_type,
            subject=subject or '',
            category=category,
            difficulty_level=difficulty_level,
            tags=tags,
            created_by=created_by,
            suggested_marks=marks,
            expected_answer=expected_answer,
            marking_scheme=marking_scheme,
            is_active=True,
        )

        # Create Question
        question = Question.objects.create(
            exam=exam,
            question_bank=bank,
            question_text=question_text,
            question_type=question_type,
            marks=marks,
            question_order=question_order,
            is_required=is_required,
            expected_answer=expected_answer,
            marking_scheme=marking_scheme,
            created_by=created_by,
        )

        # Create options for both QuestionBank and Question
        for idx, opt in enumerate(options, start=1):
            bank_option = QuestionBankOption.objects.create(
                question_bank=bank,
                option_text=opt['option_text'],
                is_correct=opt.get('is_correct', False),
                option_order=idx,
                explanation=opt.get('explanation', ''),
            )
            QuestionOption.objects.create(
                question=question,
                bank_option=bank_option,
                option_text=opt['option_text'],
                is_correct=opt.get('is_correct', False),
                option_order=idx,
                explanation=opt.get('explanation', ''),
            )
        return question

    @staticmethod
    @transaction.atomic
    def update_question_new(
        question: Question,
        question_text: str,
        marks: float,
        is_required: bool,
        expected_answer: str,
        marking_scheme: str,
        options: List[Dict[str, Any]],
    ) -> Question:
        question.question_text = question_text
        question.marks = marks
        question.is_required = is_required
        question.expected_answer = expected_answer
        question.marking_scheme = marking_scheme
        question.save()

        # Update options: delete old, create new
        question.options.all().delete()
        for idx, opt in enumerate(options, start=1):
            QuestionOption.objects.create(
                question=question,
                option_text=opt['option_text'],
                is_correct=opt.get('is_correct', False),
                option_order=idx,
                explanation=opt.get('explanation', ''),
            )
        return question


    @staticmethod
    @transaction.atomic
    def delete_question(question_id: int) -> bool:
        """Delete an exam question"""

        question = QuestionSelector.get_by_id(question_id)
        if not question:
            raise ValidationError("Question not found")

        # Check if exam is active or has submissions
        # This would depend on your exam and submission models

        question.delete()
        return True

    @staticmethod
    @transaction.atomic
    def reorder_questions(exam_id: int, question_orders: List[Dict[str, Any]]) -> List[Question]:
        """Reorder questions in an exam"""

        questions = []
        for order_data in question_orders:
            question_id = order_data.get('question_id')
            new_order = order_data.get('order')
            
            question = QuestionSelector.get_by_id(question_id)
            if not question or question.exam_id != exam_id:
                raise ValidationError(f"Invalid question ID: {question_id}")
            
            question.question_order = new_order
            question.save()
            questions.append(question)

        return questions


class QuestionOptionService:
    """Service for QuestionOption operations"""

    @staticmethod
    @transaction.atomic
    def create_option(
        question_id: int,
        option_text: str,
        is_correct: bool = False,
        option_order: int = 1,
        explanation: str = ""
    ) -> QuestionOption:
        """Create a new option for an exam question"""

        question = QuestionSelector.get_by_id(question_id)
        if not question:
            raise ValidationError("Question not found")

        if question.question_type not in ['mcq', 'true_false']:
            raise ValidationError("Options can only be added to MCQ or True/False questions")

        # Check if option order already exists
        if QuestionOption.objects.filter(
            question_id=question_id, 
            option_order=option_order
        ).exists():
            raise ValidationError(f"Option with order {option_order} already exists")

        option = QuestionOption.objects.create(
            question=question,
            option_text=option_text,
            is_correct=is_correct,
            option_order=option_order,
            explanation=explanation
        )

        return option

    @staticmethod
    @transaction.atomic
    def create_options_for_question(
        question_id: int, 
        options_data: List[Dict[str, Any]]
    ) -> List[QuestionOption]:
        """Create multiple options for a question"""

        question = QuestionSelector.get_by_id(question_id)
        if not question:
            raise ValidationError("Question not found")

        if question.question_type not in ['mcq', 'true_false']:
            raise ValidationError("Options can only be added to MCQ or True/False questions")

        # Delete existing options
        QuestionOption.objects.filter(question_id=question_id).delete()

        options = []
        for option_data in options_data:
            option = QuestionOption.objects.create(
                question=question,
                option_text=option_data.get('option_text', ''),
                is_correct=option_data.get('is_correct', False),
                option_order=option_data.get('option_order', len(options) + 1),
                explanation=option_data.get('explanation', '')
            )
            options.append(option)

        return options

    @staticmethod
    @transaction.atomic
    def update_option(
        option_id: int,
        option_text: Optional[str] = None,
        is_correct: Optional[bool] = None,
        explanation: Optional[str] = None
    ) -> QuestionOption:
        """Update an existing option"""

        option = QuestionOptionSelector.get_by_id(option_id)
        if not option:
            raise ValidationError("Option not found")

        if option_text is not None:
            option.option_text = option_text
        if is_correct is not None:
            option.is_correct = is_correct
        if explanation is not None:
            option.explanation = explanation

        option.save()
        return option

    @staticmethod
    @transaction.atomic
    def delete_option(option_id: int) -> bool:
        """Delete an option"""

        option = QuestionOptionSelector.get_by_id(option_id)
        if not option:
            raise ValidationError("Option not found")

        option.delete()
        return True