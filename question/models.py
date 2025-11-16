from django.db import models
from django.core.exceptions import ValidationError
from django.dispatch import receiver
from exam.utils import IDGenerator
from account.models import User
from django.db.models.signals import pre_save
from academy.choices_fields import SUBJECT_TYPE_CHOICES, SUBJECT_TYPE_BANGLA
from classmate.models import ClassMateModel

class QuestionBankCategory(ClassMateModel):
    """Categories for organizing questions in the question bank"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent_category = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    
    # Category metadata
    category_id = models.CharField(max_length=20, unique=True, editable=False, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_categories')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Question Category'
        verbose_name_plural = 'Question Categories'
        ordering = ['name']

    def __str__(self):
        if self.parent_category:
            return f'{self.parent_category.name} > {self.name}'
        return self.name
    

class QuestionBank(ClassMateModel):
    """Central repository for all questions that can be reused across exams"""
    title = models.CharField(max_length=255, help_text='Question title or summary')
    question_text = models.TextField(help_text='The actual question text')
    
    QUESTION_TYPE_CHOICES = [
        ('mcq', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
        ('essay', 'Essay'),
    ]
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default='mcq')
    
    subject = models.CharField(
        max_length=50,
        choices=SUBJECT_TYPE_CHOICES,
        default=SUBJECT_TYPE_BANGLA,
        help_text="Subject"
    )
    category = models.ForeignKey(
        QuestionBankCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='questions',
        help_text='Category for organizing questions'
    )
    # Difficulty and categorization
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    difficulty_level = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    
    # Tags for better organization
    tags = models.CharField(max_length=500, blank=True, help_text='Comma-separated tags (e.g., "algebra, equations, chapter-1")')
    
    # Question metadata
    question_bank_id = models.CharField(max_length=20, unique=True, editable=False, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_bank_questions')
    suggested_marks = models.DecimalField(max_digits=5, decimal_places=2, default=1.0, help_text='Suggested marks for this question')
    
    # Usage tracking
    usage_count = models.PositiveIntegerField(default=0, help_text='Number of times this question has been used in exams')
    last_used_at = models.DateTimeField(null=True, blank=True, help_text='When this question was last used')
    
    # Quality control
    is_approved = models.BooleanField(default=False, help_text='Whether question is approved for use')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_bank_questions')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # For essay/short answer questions
    expected_answer = models.TextField(blank=True, help_text='Expected answer or answer guidelines')
    marking_scheme = models.TextField(blank=True, help_text='Detailed marking scheme for subjective questions')
    
    # Status
    is_active = models.BooleanField(default=True, help_text='Whether question is active and available for use')
    
    class Meta:
        verbose_name = 'Question Bank'
        verbose_name_plural = 'Question Bank'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['subject', 'question_type']),
            models.Index(fields=['difficulty_level']),
            models.Index(fields=['is_approved', 'is_active']),
        ]

    def __str__(self):
        return f'{self.title} ({self.get_question_type_display()}) - {self.subject}'

    @property
    def tag_list(self):
        """Return tags as a list"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []

    @property
    def is_mcq_or_true_false(self):
        """Check if question requires options"""
        return self.question_type in ['mcq', 'true_false']

    def increment_usage(self):
        """Increment usage count and update last used timestamp"""
        from django.utils import timezone
        self.usage_count += 1
        self.last_used_at = timezone.now()
        self.save(update_fields=['usage_count', 'last_used_at'])


class QuestionBankOption(ClassMateModel):
    """Options for MCQ and True/False questions in question bank"""
    question_bank = models.ForeignKey(QuestionBank, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=500, help_text='Option text')
    is_correct = models.BooleanField(default=False, help_text='Whether this option is correct')
    option_order = models.PositiveIntegerField(help_text='Order of option (1, 2, 3, 4...)')
    explanation = models.TextField(blank=True, help_text='Explanation for why this option is correct/incorrect')

    class Meta:
        verbose_name = 'Question Bank Option'
        verbose_name_plural = 'Question Bank Options'
        ordering = ['question_bank', 'option_order']
        constraints = [
            models.UniqueConstraint(fields=['question_bank', 'option_order'], name='unique_bank_option_order_per_question')
        ]

    def __str__(self):
        option_labels = ['A', 'B', 'C', 'D', 'E', 'F']
        label = option_labels[self.option_order - 1] if self.option_order <= len(option_labels) else str(self.option_order)
        return f'{label}. {self.option_text}'

    def clean(self):
        """Validate option data"""
        if self.question_bank and not self.question_bank.is_mcq_or_true_false:
            raise ValidationError('Options can only be added to MCQ or True/False questions.')
    

class Question(ClassMateModel):
    """Model for exam questions"""
    QUESTION_TYPE_CHOICES = [
        ('mcq', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
        ('essay', 'Essay'),
    ]
    exam = models.ForeignKey('exam.Exam', on_delete=models.CASCADE, related_name='questions')

    # Reference to question bank (optional)
    question_bank = models.ForeignKey(QuestionBank, on_delete=models.SET_NULL, null=True, blank=True, related_name='exam_questions')
    
    # Question content (can be copied from bank or entered fresh)
    question_text = models.TextField(help_text='The question text')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default='mcq')
    marks = models.DecimalField(max_digits=5, decimal_places=2, help_text='Marks for this question')
    question_order = models.PositiveIntegerField(help_text='Order of question in exam')
    is_required = models.BooleanField(default=True, help_text='Whether this question is mandatory')
    
    # For essay/short answer questions
    expected_answer = models.TextField(blank=True, help_text='Expected answer (for reference)')
    marking_scheme = models.TextField(blank=True, help_text='Marking scheme for this question')

    # Question metadata
    question_id = models.CharField(max_length=20, unique=True, help_text='Unique ID for the Question', editable=False, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_questions')

    class Meta:
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
        ordering = ['exam', 'question_order']
        constraints = [
            models.UniqueConstraint(fields=['exam', 'question_order'], name='unique_question_order_per_exam')
        ]

    def __str__(self):
        return f'{self.exam.title} - Q{self.question_order}: {self.question_text[:50]}...'

    def clean(self):
        """Validate question data"""
        if self.exam and self.exam.exam_type != 'online':
            raise ValidationError('Questions can only be added to online exams.')
        
    def save(self, *args, **kwargs):
        """Copy data from question bank if referenced and increment usage"""
        if self.question_bank and not self.pk:  # Only on creation
            # Copy data from question bank
            self.question_text = self.question_bank.question_text
            self.question_type = self.question_bank.question_type
            self.expected_answer = self.question_bank.expected_answer
            self.marking_scheme = self.question_bank.marking_scheme
            
            # Use suggested marks if marks not set
            if not self.marks:
                self.marks = self.question_bank.suggested_marks
        
        super().save(*args, **kwargs)
        
        # Increment usage count in question bank
        if self.question_bank:
            self.question_bank.increment_usage()

    @property
    def is_from_bank(self):
        """Check if question is from question bank"""
        return self.question_bank is not None


class QuestionOption(ClassMateModel):
    """Model for multiple choice question options"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    
    # Reference to bank option (optional)
    bank_option = models.ForeignKey(QuestionBankOption, on_delete=models.SET_NULL, null=True, blank=True)
    
    option_text = models.CharField(max_length=500, help_text='Option text')
    is_correct = models.BooleanField(default=False, help_text='Whether this option is correct')
    option_order = models.PositiveIntegerField(help_text='Order of option (A, B, C, D)')
    explanation = models.TextField(blank=True, help_text='Explanation for this option')

    class Meta:
        verbose_name = 'Question Option'
        verbose_name_plural = 'Question Options'
        ordering = ['question', 'option_order']
        constraints = [
            models.UniqueConstraint(fields=['question', 'option_order'], name='unique_option_order_per_question')
        ]

    def __str__(self):
        option_labels = ['A', 'B', 'C', 'D', 'E', 'F']
        label = option_labels[self.option_order - 1] if self.option_order <= len(option_labels) else str(self.option_order)
        return f'{label}. {self.option_text}'

    def clean(self):
        """Validate option data"""
        if self.question and self.question.question_type not in ['mcq', 'true_false']:
            raise ValidationError('Options can only be added to MCQ or True/False questions.')
    
    def save(self, *args, **kwargs):
        """Copy data from bank option if referenced"""
        if self.bank_option and not self.pk:  # Only on creation
            self.option_text = self.bank_option.option_text
            self.is_correct = self.bank_option.is_correct
            self.explanation = self.bank_option.explanation
        
        super().save(*args, **kwargs)


@receiver(pre_save, sender=Question)
def set_question_id_on_create(sender, instance, **kwargs):
    """Signal to auto-generate question_id only when creating a new Question."""
    if (not instance.pk and not instance.question_id) or (instance.pk and not instance.question_id):
        instance.question_id = IDGenerator.generate_question_id()

# Add signals for auto-generating IDs
@receiver(pre_save, sender=QuestionBank)
def set_question_bank_id_on_create(sender, instance, **kwargs):
    """Signal to auto-generate question_bank_id only when creating a new QuestionBank."""
    if (not instance.pk and not instance.question_bank_id) or (instance.pk and not instance.question_bank_id):
        instance.question_bank_id = IDGenerator.generate_question_bank_id()


@receiver(pre_save, sender=QuestionBankCategory)
def set_category_id_on_create(sender, instance, **kwargs):
    """Signal to auto-generate category_id only when creating a new Category."""
    if (not instance.pk and not instance.category_id) or (instance.pk and not instance.category_id):
        instance.category_id = IDGenerator.generate_category_id()
