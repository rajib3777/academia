from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from rest_framework.views import APIView
from functools import cached_property
from classmate.permissions import AuthenticatedGenericView
from django.core.exceptions import ValidationError
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
import json
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render, redirect
from django.contrib import messages
from question.selectors.question_selector import (
    QuestionBankCategorySelector,
    QuestionBankSelector, 
    QuestionSelector,
    QuestionOptionSelector,
    QuestionBankOptionSelector
)
from question.services.question_service import (
    QuestionBankCategoryService,
    QuestionBankService,
    QuestionService,
    QuestionOptionService,
    QuestionBankOptionService
)

from question.serializers.question_serializer import (
    QuestionBankCategoryListSerializer,
    QuestionBankCategoryDetailSerializer,
    QuestionBankCategoryCreateSerializer,
    QuestionBankListSerializer,
    QuestionBankDetailSerializer,
    QuestionBankCreateSerializer,
    QuestionListSerializer,
    QuestionDetailSerializer,
    QuestionCreateFromBankSerializer,
    QuestionCreateCustomSerializer,
    QuestionOptionSerializer,
    QuestionSerializer
)

class QuestionBankCategoryListView(AuthenticatedGenericView, APIView):
    """List all question bank categories"""
    
    selector_class = QuestionBankCategorySelector
    template_name = 'question/category/list.html'
    htmx_template_name = 'question/category/_htmx_category_list.html'

    def get(self, request):
        """Get category list"""
        search_term = request.GET.get('search', '').strip()
        show_inactive = request.GET.get('show_inactive') == 'true'
        
        try:
            if search_term:
                categories = self.selector_class.search_categories(search_term)
            else:
                categories = self.selector_class.get_categories_with_question_count()
            
            if not show_inactive:
                categories = categories.filter(is_active=True)
            
            # Serialize data
            serializer = QuestionBankCategoryListSerializer()
            categories_data = [serializer.to_representation(category) for category in categories]
            
        except Exception as e:
            return


class QuestionBankCategoryDetailView(AuthenticatedGenericView, APIView):
    """Detail view for question bank category"""
    
    selector_class = QuestionBankCategorySelector
    template_name = 'question/category/detail.html'
    htmx_template_name = 'question/category/_htmx_category_detail.html'

    def get(self, request, category_id: int):
        """Get category detail"""
        try:
            category = self.selector_class.get_by_id(category_id)
            if not category:
                return self.handle_error_response('Category not found', status=404)
            
            # Serialize data
            serializer = QuestionBankCategoryDetailSerializer()
            category_data = serializer.to_representation(category)
            return
        except Exception as e:
            return


class QuestionBankCategoryCreateView(AuthenticatedGenericView, APIView):
    """Create new question bank category"""
    
    service_class = QuestionBankCategoryService
    template_name = 'question/category/create.html'
    htmx_template_name = 'question/category/_htmx_category_form.html'

    def get(self, request):
        """Show create form"""
        parent_categories = QuestionBankCategorySelector.list_active_categories()
        
        return

    def post(self, request):
        """Create category"""
        try:
            serializer = QuestionBankCategoryCreateSerializer(data=request.POST)
            if not serializer.is_valid():
                error_message = ' '.join([f'{field}: {", ".join(errors)}' for field, errors in serializer.errors.items()])
                return self.handle_error_response(f'Validation error: {error_message}')
            
            # Create category
            category = self.service_class.create_category(
                name=serializer.validated_data['name'],
                description=serializer.validated_data.get('description', ''),
                parent_category_id=serializer.validated_data.get('parent_category_id'),
                created_by=request.user
            )
            
            if request.htmx:
                # Return updated list
                categories = QuestionBankCategorySelector.get_categories_with_question_count()
                categories_data = [
                    QuestionBankCategoryListSerializer().to_representation(cat) 
                    for cat in categories
                ]
                
                context = self.get_context_data(categories=categories_data)
                return self.handle_htmx_response(
                    'question/category/_htmx_category_list.html',
                    context,
                    trigger={'categoryCreated': {'message': f'Category "{category.name}" created successfully'}}
                )
            else:
                messages.success(request, f'Category "{category.name}" created successfully')
                return redirect('question:category-detail', category_id=category.id)
                
        except ValidationError as e:
            return self.handle_error_response(str(e))
        except Exception as e:
            return self.handle_error_response(f'Error creating category: {str(e)}')


class QuestionBankCategoryUpdateView(AuthenticatedGenericView, APIView):
    """Update question bank category"""
    
    selector_class = QuestionBankCategorySelector
    service_class = QuestionBankCategoryService
    template_name = 'question/category/update.html'
    htmx_template_name = 'question/category/_htmx_category_form.html'

    def get(self, request, category_id: int):
        """Show update form"""
        try:
            category = self.selector_class.get_by_id(category_id)
            if not category:
                return self.handle_error_response('Category not found', status=404)
            
            parent_categories = QuestionBankCategorySelector.list_active_categories().exclude(id=category_id)
            
            return
        except Exception as e:
            return

    def post(self, request, category_id: int):
        """Update category"""
        try:
            category = self.selector_class.get_by_id(category_id)
            if not category:
                return self.handle_error_response('Category not found', status=404)
            
            # Update category
            updated_category = self.service_class.update_category(
                category_id=category_id,
                name=request.POST.get('name'),
                description=request.POST.get('description'),
                parent_category_id=request.POST.get('parent_category_id') or None,
                is_active=request.POST.get('is_active') == 'on'
            )
            
            if request.htmx:
                # Return updated detail view
                serializer = QuestionBankCategoryDetailSerializer()
                category_data = serializer.to_representation(updated_category)
                
                context = self.get_context_data(category=category_data)
                return self.handle_htmx_response(
                    'question/category/_htmx_category_detail.html',
                    context,
                    trigger={'categoryUpdated': {'message': f'Category "{updated_category.name}" updated successfully'}}
                )
            else:
                messages.success(request, f'Category "{updated_category.name}" updated successfully')
                return redirect('question:category-detail', category_id=updated_category.id)
                
        except ValidationError as e:
            return self.handle_error_response(str(e))
        except Exception as e:
            return self.handle_error_response(f'Error updating category: {str(e)}')


class QuestionBankCategoryDeleteView(AuthenticatedGenericView, APIView):
    """Delete question bank category"""
    
    service_class = QuestionBankCategoryService

    def post(self, request, category_id: int):
        """Delete category (soft delete)"""
        try:
            result = self.service_class.delete_category(category_id)
            
            if request.htmx:
                # Return updated list
                categories = QuestionBankCategorySelector.get_categories_with_question_count().filter(is_active=True)
                categories_data = [
                    QuestionBankCategoryListSerializer().to_representation(cat) 
                    for cat in categories
                ]
                
                context = self.get_context_data(categories=categories_data)
                return self.handle_htmx_response(
                    'question/category/_htmx_category_list.html',
                    context,
                    trigger={'categoryDeleted': {'message': 'Category deleted successfully'}}
                )
            else:
                messages.success(request, 'Category deleted successfully')
                return redirect('question:category-list')
                
        except ValidationError as e:
            return self.handle_error_response(str(e))
        except Exception as e:
            return self.handle_error_response(f'Error deleting category: {str(e)}')


class QuestionBankListView(AuthenticatedGenericView, APIView):
    """List question bank questions with filtering and pagination"""
    
    selector_class = QuestionBankSelector
    template_name = 'question/bank/list.html'
    htmx_template_name = 'question/bank/_htmx_question_list.html'

    def get(self, request):
        """Get question bank list with filters"""
        # Get filter parameters
        page_number = request.GET.get('page', 1)
        search_term = request.GET.get('search', '').strip()
        subject = request.GET.get('subject')
        question_type = request.GET.get('question_type')
        difficulty_level = request.GET.get('difficulty_level')
        category_id = request.GET.get('category_id')
        is_approved = request.GET.get('is_approved')
        
        # Parse is_approved filter
        approved_filter = None
        if is_approved == 'true':
            approved_filter = True
        elif is_approved == 'false':
            approved_filter = False
        
        try:
            # Get paginated questions
            questions, total_count, paginator, page, page_range = self.selector_class.list_questions_paginated(
                page=page_number,
                per_page=10,
                subject=subject,
                question_type=question_type,
                difficulty_level=difficulty_level,
                category_id=int(category_id) if category_id else None,
                search_term=search_term
            )
            
            # Apply approval filter if needed
            if approved_filter is not None:
                questions = questions.filter(is_approved=approved_filter)
                total_count = questions.count()
            
            # Serialize data
            serializer = QuestionBankListSerializer()
            questions_data = [serializer.to_representation(question) for question in questions]
            
            # Get filter options
            categories = QuestionBankCategorySelector.list_active_categories()
            
            context = self.get_context_data(
                questions=questions_data,
                categories=categories,
                total_count=total_count,
                current_page=page.number,
                start_item=page.start_index(),
                end_item=page.end_index(),
                has_next=page.has_next(),
                page_range=page_range,
                last_page=paginator.num_pages,
                search_term=search_term,
                filters={
                    'subject': subject,
                    'question_type': question_type,
                    'difficulty_level': difficulty_level,
                    'category_id': category_id,
                    'is_approved': is_approved,
                },
                hx_get_api='question/bank/',
                hx_target_id='question-bank-list'
            )
            
            if request.htmx:
                return self.handle_htmx_response(self.htmx_template_name, context)
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            return self.handle_error_response(f'Error loading questions: {str(e)}')


class QuestionBankDetailView(AuthenticatedGenericView, APIView):
    """Detail view for question bank question"""
    
    selector_class = QuestionBankSelector
    template_name = 'question/bank/detail.html'
    htmx_template_name = 'question/bank/_htmx_question_detail.html'

    def get(self, request, question_id: int):
        """Get question detail"""
        try:
            question = self.selector_class.get_by_id(question_id)
            if not question:
                return self.handle_error_response('Question not found', status=404)
            
            # Serialize data
            serializer = QuestionBankDetailSerializer()
            question_data = serializer.to_representation(question)
            
            context = self.get_context_data(
                question=question_data,
                question_obj=question
            )
            
            if request.htmx:
                return self.handle_htmx_response(self.htmx_template_name, context)
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            return self.handle_error_response(f'Error loading question: {str(e)}')


class QuestionBankCreateView(AuthenticatedGenericView, APIView):
    """Create new question bank question"""
    
    service_class = QuestionBankService
    template_name = 'question/bank/create.html'
    htmx_template_name = 'question/bank/_htmx_question_form.html'

    def get(self, request):
        """Show create form"""
        categories = QuestionBankCategorySelector.list_active_categories()
        
        context = self.get_context_data(
            categories=categories,
            form_action='create',
            question_types=[
                ('mcq', 'Multiple Choice'),
                ('true_false', 'True/False'),
                ('short_answer', 'Short Answer'),
                ('essay', 'Essay'),
            ],
            difficulty_levels=[
                ('easy', 'Easy'),
                ('medium', 'Medium'),
                ('hard', 'Hard'),
            ]
        )
        
        if request.htmx:
            return self.handle_htmx_response(self.htmx_template_name, context)
        
        return render(request, self.template_name, context)

    def post(self, request):
        """Create question"""
        try:
            # Parse form data
            form_data = request.POST.copy()
            
            # Handle options for MCQ/True-False questions
            options_data = []
            question_type = form_data.get('question_type')
            
            if question_type in ['mcq', 'true_false']:
                option_count = int(form_data.get('option_count', 0))
                for i in range(1, option_count + 1):
                    option_text = form_data.get(f'option_{i}_text')
                    is_correct = form_data.get(f'option_{i}_correct') == 'on'
                    explanation = form_data.get(f'option_{i}_explanation', '')
                    
                    if option_text:
                        options_data.append({
                            'option_text': option_text,
                            'is_correct': is_correct,
                            'option_order': i,
                            'explanation': explanation
                        })
            
            # Create question
            question = self.service_class.create_question(
                title=form_data.get('title'),
                question_text=form_data.get('question_text'),
                question_type=form_data.get('question_type'),
                subject=form_data.get('subject'),
                difficulty_level=form_data.get('difficulty_level', 'medium'),
                category_id=int(form_data.get('category_id')) if form_data.get('category_id') else None,
                tags=form_data.get('tags', ''),
                suggested_marks=float(form_data.get('suggested_marks', 1.0)),
                expected_answer=form_data.get('expected_answer', ''),
                marking_scheme=form_data.get('marking_scheme', ''),
                created_by=request.user,
                options_data=options_data
            )
            
            if request.htmx:
                # Return updated list or redirect to detail
                return self.handle_htmx_response(
                    'question/bank/_htmx_success_message.html',
                    {'message': f'Question "{question.title}" created successfully', 'redirect_url': f'/question/bank/{question.id}/'},
                    trigger={'questionCreated': {'question_id': question.id}}
                )
            else:
                messages.success(request, f'Question "{question.title}" created successfully')
                return redirect('question:bank-detail', question_id=question.id)
                
        except ValidationError as e:
            return self.handle_error_response(str(e))
        except Exception as e:
            return self.handle_error_response(f'Error creating question: {str(e)}')


class QuestionBankUpdateView(AuthenticatedGenericView, APIView):
    """Update question bank question"""
    
    selector_class = QuestionBankSelector
    service_class = QuestionBankService
    template_name = 'question/bank/update.html'
    htmx_template_name = 'question/bank/_htmx_question_form.html'

    def get(self, request, question_id: int):
        """Show update form"""
        try:
            question = self.selector_class.get_by_id(question_id)
            if not question:
                return self.handle_error_response('Question not found', status=404)
            
            categories = QuestionBankCategorySelector.list_active_categories()
            
            context = self.get_context_data(
                question=question,
                categories=categories,
                form_action='update'
            )
            
            if request.htmx:
                return self.handle_htmx_response(self.htmx_template_name, context)
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            return self.handle_error_response(f'Error loading question: {str(e)}')

    def post(self, request, question_id: int):
        """Update question"""
        try:
            form_data = request.POST.copy()
            
            # Update question
            updated_question = self.service_class.update_question(
                question_id=question_id,
                title=form_data.get('title'),
                question_text=form_data.get('question_text'),
                question_type=form_data.get('question_type'),
                subject=form_data.get('subject'),
                difficulty_level=form_data.get('difficulty_level'),
                category_id=int(form_data.get('category_id')) if form_data.get('category_id') else None,
                tags=form_data.get('tags'),
                suggested_marks=float(form_data.get('suggested_marks')) if form_data.get('suggested_marks') else None,
                expected_answer=form_data.get('expected_answer'),
                marking_scheme=form_data.get('marking_scheme'),
                is_active=form_data.get('is_active') == 'on'
            )
            
            if request.htmx:
                # Return updated detail view
                serializer = QuestionBankDetailSerializer()
                question_data = serializer.to_representation(updated_question)
                
                context = self.get_context_data(question=question_data)
                return self.handle_htmx_response(
                    'question/bank/_htmx_question_detail.html',
                    context,
                    trigger={'questionUpdated': {'message': f'Question "{updated_question.title}" updated successfully'}}
                )
            else:
                messages.success(request, f'Question "{updated_question.title}" updated successfully')
                return redirect('question:bank-detail', question_id=updated_question.id)
                
        except ValidationError as e:
            return self.handle_error_response(str(e))
        except Exception as e:
            return self.handle_error_response(f'Error updating question: {str(e)}')


class QuestionBankApproveView(AuthenticatedGenericView, APIView):
    """Approve/unapprove question bank question"""
    
    service_class = QuestionBankService

    def post(self, request, question_id: int):
        """Toggle question approval"""
        try:
            action = request.POST.get('action')  # 'approve' or 'unapprove'
            
            if action == 'approve':
                question = self.service_class.approve_question(question_id, request.user)
                message = f'Question "{question.title}" approved successfully'
            else:
                question = self.service_class.unapprove_question(question_id)
                message = f'Question "{question.title}" approval removed'
            
            if request.htmx:
                # Return updated question detail
                serializer = QuestionBankDetailSerializer()
                question_data = serializer.to_representation(question)
                
                context = self.get_context_data(question=question_data)
                return self.handle_htmx_response(
                    'question/bank/_htmx_question_detail.html',
                    context,
                    trigger={'questionApprovalChanged': {'message': message}}
                )
            else:
                messages.success(request, message)
                return redirect('question:bank-detail', question_id=question.id)
                
        except ValidationError as e:
            return self.handle_error_response(str(e))
        except Exception as e:
            return self.handle_error_response(f'Error updating approval: {str(e)}')


class QuestionBankDuplicateView(AuthenticatedGenericView, APIView):
    """Duplicate question bank question"""
    
    service_class = QuestionBankService

    def post(self, request, question_id: int):
        """Duplicate question"""
        try:
            duplicated_question = self.service_class.duplicate_question(
                question_id=question_id,
                created_by=request.user
            )
            
            if request.htmx:
                return self.handle_htmx_response(
                    'question/bank/_htmx_success_message.html',
                    {
                        'message': f'Question duplicated successfully',
                        'redirect_url': f'/question/bank/{duplicated_question.id}/'
                    },
                    trigger={'questionDuplicated': {'question_id': duplicated_question.id}}
                )
            else:
                messages.success(request, f'Question duplicated successfully')
                return redirect('question:bank-detail', question_id=duplicated_question.id)
                
        except ValidationError as e:
            return self.handle_error_response(str(e))
        except Exception as e:
            return self.handle_error_response(f'Error duplicating question: {str(e)}')


class ExamQuestionListView(AuthenticatedGenericView, APIView):
    """List questions for a specific exam"""
    
    selector_class = QuestionSelector
    template_name = 'question/exam/list.html'
    htmx_template_name = 'question/exam/_htmx_question_list.html'

    def get(self, request, exam_id: int):
        """Get exam questions"""
        try:
            questions = self.selector_class.get_questions_with_options(exam_id)
            
            # Serialize data
            serializer = QuestionListSerializer()
            questions_data = [serializer.to_representation(question) for question in questions]
            
            # Get question type counts and total marks
            question_counts = self.selector_class.count_questions_by_type(exam_id)
            total_marks = self.selector_class.get_total_marks(exam_id)
            
            context = self.get_context_data(
                exam_id=exam_id,
                questions=questions_data,
                question_counts=question_counts,
                total_marks=total_marks,
                total_questions=len(questions_data)
            )
            
            if request.htmx:
                return self.handle_htmx_response(self.htmx_template_name, context)
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            return self.handle_error_response(f'Error loading exam questions: {str(e)}')


class ExamQuestionDetailView(AuthenticatedGenericView, APIView):
    """Detail view for exam question"""
    
    selector_class = QuestionSelector
    template_name = 'question/exam/detail.html'
    htmx_template_name = 'question/exam/_htmx_question_detail.html'

    def get(self, request, question_id: int):
        """Get question detail"""
        try:
            question = self.selector_class.get_by_id(question_id)
            if not question:
                return self.handle_error_response('Question not found', status=404)
            
            # Serialize data
            serializer = QuestionDetailSerializer()
            question_data = serializer.to_representation(question)
            
            context = self.get_context_data(
                question=question_data,
                question_obj=question
            )
            
            if request.htmx:
                return self.handle_htmx_response(self.htmx_template_name, context)
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            return self.handle_error_response(f'Error loading question: {str(e)}')


class ExamQuestionCreateFromBankView(AuthenticatedGenericView, APIView):
    """Create exam question from question bank"""
    
    service_class = QuestionService
    template_name = 'question/exam/create_from_bank.html'
    htmx_template_name = 'question/exam/_htmx_bank_question_form.html'

    def get(self, request, exam_id: int):
        """Show question bank selection"""
        # Get approved bank questions
        bank_questions = QuestionBankSelector.list_approved_questions()
        
        # Filter parameters
        subject = request.GET.get('subject')
        question_type = request.GET.get('question_type')
        difficulty = request.GET.get('difficulty')
        category_id = request.GET.get('category_id')
        search_term = request.GET.get('search')
        
        if any([subject, question_type, difficulty, category_id, search_term]):
            bank_questions = QuestionBankSelector.filter_questions(
                subject=subject,
                question_type=question_type,
                difficulty_level=difficulty,
                category_id=int(category_id) if category_id else None,
                search_term=search_term,
                is_approved=True
            )
        
        context = self.get_context_data(
            exam_id=exam_id,
            bank_questions=bank_questions[:20],  # Limit for initial load
            filters={
                'subject': subject,
                'question_type': question_type,
                'difficulty': difficulty,
                'category_id': category_id,
                'search': search_term,
            }
        )
        
        if request.htmx:
            return self.handle_htmx_response(self.htmx_template_name, context)
        
        return render(request, self.template_name, context)

    def post(self, request, exam_id: int):
        """Add question from bank to exam"""
        try:
            serializer = QuestionCreateFromBankSerializer(data=request.POST)
            if not serializer.is_valid():
                error_message = ' '.join([f'{field}: {", ".join(errors)}' for field, errors in serializer.errors.items()])
                return self.handle_error_response(f'Validation error: {error_message}')
            
            # Create question from bank
            question = self.service_class.create_question_from_bank(
                exam_id=exam_id,
                question_bank_id=serializer.validated_data['question_bank_id'],
                marks=serializer.validated_data.get('marks'),
                question_order=serializer.validated_data.get('question_order'),
                is_required=serializer.validated_data.get('is_required', True)
            )
            
            if request.htmx:
                # Return updated exam question list
                questions = QuestionSelector.get_questions_with_options(exam_id)
                questions_data = [QuestionListSerializer().to_representation(q) for q in questions]
                
                context = self.get_context_data(
                    exam_id=exam_id,
                    questions=questions_data
                )
                return self.handle_htmx_response(
                    'question/exam/_htmx_question_list.html',
                    context,
                    trigger={'questionAdded': {'message': 'Question added to exam successfully'}}
                )
            else:
                messages.success(request, 'Question added to exam successfully')
                return redirect('question:exam-question-list', exam_id=exam_id)
                
        except ValidationError as e:
            return self.handle_error_response(str(e))
        except Exception as e:
            return self.handle_error_response(f'Error adding question: {str(e)}')


class ExamQuestionCreateCustomView(AuthenticatedGenericView, APIView):
    """Create custom exam question (not from bank)"""
    
    service_class = QuestionService
    template_name = 'question/exam/create_custom.html'
    htmx_template_name = 'question/exam/_htmx_custom_question_form.html'

    def get(self, request, exam_id: int):
        """Show custom question form"""
        context = self.get_context_data(
            exam_id=exam_id,
            form_action='create',
            question_types=[
                ('mcq', 'Multiple Choice'),
                ('true_false', 'True/False'),
                ('short_answer', 'Short Answer'),
                ('essay', 'Essay'),
            ]
        )
        
        if request.htmx:
            return self.handle_htmx_response(self.htmx_template_name, context)
        
        return render(request, self.template_name, context)

    def post(self, request, exam_id: int):
        """Create custom question"""
        try:
            form_data = request.POST.copy()
            
            # Handle options for MCQ/True-False questions
            options_data = []
            question_type = form_data.get('question_type')
            
            if question_type in ['mcq', 'true_false']:
                option_count = int(form_data.get('option_count', 0))
                for i in range(1, option_count + 1):
                    option_text = form_data.get(f'option_{i}_text')
                    is_correct = form_data.get(f'option_{i}_correct') == 'on'
                    explanation = form_data.get(f'option_{i}_explanation', '')
                    
                    if option_text:
                        options_data.append({
                            'option_text': option_text,
                            'is_correct': is_correct,
                            'option_order': i,
                            'explanation': explanation
                        })
            
            # Create custom question
            question = self.service_class.create_custom_question(
                exam_id=exam_id,
                question_text=form_data.get('question_text'),
                question_type=form_data.get('question_type'),
                marks=float(form_data.get('marks')),
                question_order=int(form_data.get('question_order')) if form_data.get('question_order') else None,
                is_required=form_data.get('is_required') == 'on',
                expected_answer=form_data.get('expected_answer', ''),
                marking_scheme=form_data.get('marking_scheme', ''),
                created_by=request.user,
                options_data=options_data
            )
            
            if request.htmx:
                # Return updated exam question list
                questions = QuestionSelector.get_questions_with_options(exam_id)
                questions_data = [QuestionListSerializer().to_representation(q) for q in questions]
                
                context = self.get_context_data(
                    exam_id=exam_id,
                    questions=questions_data
                )
                return self.handle_htmx_response(
                    'question/exam/_htmx_question_list.html',
                    context,
                    trigger={'questionCreated': {'message': 'Custom question created successfully'}}
                )
            else:
                messages.success(request, 'Custom question created successfully')
                return redirect('question:exam-question-list', exam_id=exam_id)
                
        except ValidationError as e:
            return self.handle_error_response(str(e))
        except Exception as e:
            return self.handle_error_response(f'Error creating question: {str(e)}')


class ExamQuestionUpdateView(AuthenticatedGenericView, APIView):
    """Update exam question"""
    
    selector_class = QuestionSelector
    service_class = QuestionService
    template_name = 'question/exam/update.html'
    htmx_template_name = 'question/exam/_htmx_question_form.html'

    def get(self, request, question_id: int):
        """Show update form"""
        try:
            question = self.selector_class.get_by_id(question_id)
            if not question:
                return self.handle_error_response('Question not found', status=404)
            
            context = self.get_context_data(
                question=question,
                form_action='update'
            )
            
            if request.htmx:
                return self.handle_htmx_response(self.htmx_template_name, context)
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            return self.handle_error_response(f'Error loading question: {str(e)}')

    def post(self, request, question_id: int):
        """Update question"""
        try:
            form_data = request.POST.copy()
            
            # Update question
            updated_question = self.service_class.update_question(
                question_id=question_id,
                question_text=form_data.get('question_text'),
                marks=float(form_data.get('marks')) if form_data.get('marks') else None,
                question_order=int(form_data.get('question_order')) if form_data.get('question_order') else None,
                is_required=form_data.get('is_required') == 'on',
                expected_answer=form_data.get('expected_answer'),
                marking_scheme=form_data.get('marking_scheme')
            )
            
            if request.htmx:
                # Return updated detail view
                serializer = QuestionDetailSerializer()
                question_data = serializer.to_representation(updated_question)
                
                context = self.get_context_data(question=question_data)
                return self.handle_htmx_response(
                    'question/exam/_htmx_question_detail.html',
                    context,
                    trigger={'questionUpdated': {'message': 'Question updated successfully'}}
                )
            else:
                messages.success(request, 'Question updated successfully')
                return redirect('question:exam-question-detail', question_id=updated_question.id)
                
        except ValidationError as e:
            return self.handle_error_response(str(e))
        except Exception as e:
            return self.handle_error_response(f'Error updating question: {str(e)}')


class ExamQuestionReorderView(AuthenticatedGenericView, APIView):
    """Reorder exam questions"""
    
    service_class = QuestionService

    def post(self, request, exam_id: int):
        """Reorder questions"""
        try:
            # Parse question orders from request
            question_orders = []
            order_data = json.loads(request.body)
            
            for item in order_data.get('questions', []):
                question_orders.append({
                    'question_id': item.get('question_id'),
                    'order': item.get('order')
                })
            
            # Reorder questions
            updated_questions = self.service_class.reorder_questions(exam_id, question_orders)
            
            if request.htmx:
                # Return updated question list
                questions = QuestionSelector.get_questions_with_options(exam_id)
                questions_data = [QuestionListSerializer().to_representation(q) for q in questions]
                
                context = self.get_context_data(
                    exam_id=exam_id,
                    questions=questions_data
                )
                return self.handle_htmx_response(
                    'question/exam/_htmx_question_list.html',
                    context,
                    trigger={'questionsReordered': {'message': 'Questions reordered successfully'}}
                )
            else:
                return JsonResponse({'success': True, 'message': 'Questions reordered successfully'})
                
        except ValidationError as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error reordering questions: {str(e)}'}, status=500)


class ExamQuestionDeleteView(AuthenticatedGenericView, APIView):
    """Delete exam question"""
    
    service_class = QuestionService

    def post(self, request, question_id: int):
        """Delete question"""
        try:
            question = QuestionSelector.get_by_id(question_id)
            if not question:
                return self.handle_error_response('Question not found', status=404)
            
            exam_id = question.exam_id
            
            # Delete question
            self.service_class.delete_question(question_id)
            
            if request.htmx:
                # Return updated exam question list
                questions = QuestionSelector.get_questions_with_options(exam_id)
                questions_data = [QuestionListSerializer().to_representation(q) for q in questions]
                
                context = self.get_context_data(
                    exam_id=exam_id,
                    questions=questions_data
                )
                return self.handle_htmx_response(
                    'question/exam/_htmx_question_list.html',
                    context,
                    trigger={'questionDeleted': {'message': 'Question deleted successfully'}}
                )
            else:
                messages.success(request, 'Question deleted successfully')
                return redirect('question:exam-question-list', exam_id=exam_id)
                
        except ValidationError as e:
            return self.handle_error_response(str(e))
        except Exception as e:
            return self.handle_error_response(f'Error deleting question: {str(e)}')
        

class QuestionListCreateAPI(APIView):
    """API for listing and creating Questions."""

    def get(self, request):
        exam_id = request.query_params.get('exam_id')
        questions = QuestionSelector.list_questions(exam_id=exam_id)
        data = []
        for q in questions:
            options = QuestionSelector.get_question_options(q)
            data.append({
                'question_id': q.question_id,
                'exam_id': q.exam_id,
                'question_text': q.question_text,
                'question_type': q.question_type,
                'marks': q.marks,
                'question_order': q.question_order,
                'is_required': q.is_required,
                'expected_answer': q.expected_answer,
                'marking_scheme': q.marking_scheme,
                'options': [
                    {
                        'option_text': o.option_text,
                        'is_correct': o.is_correct,
                        'explanation': o.explanation,
                        'option_order': o.option_order,
                    } for o in options
                ],
            })
        return Response(data)

    def post(self, request):
        serializer = QuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        # You may want to validate exam ownership/permissions here
        from exam.models import Exam
        exam = get_object_or_404(Exam, pk=validated['exam_id'])

        question = QuestionService.create_question(
            exam=exam,
            question_text=validated['question_text'],
            question_type=validated['question_type'],
            marks=float(validated['marks']),
            question_order=validated['question_order'],
            is_required=validated['is_required'],
            expected_answer=validated.get('expected_answer', ''),
            marking_scheme=validated.get('marking_scheme', ''),
            created_by=request.user,
            options=validated['options'],
        )
        return Response({'question_id': question.question_id}, status=status.HTTP_201_CREATED)

class QuestionDetailUpdateDeleteAPI(APIView):
    """API for retrieving, updating, and deleting a Question."""

    def get(self, request, question_id: str):
        question = QuestionSelector.get_question(question_id)
        options = QuestionSelector.get_question_options(question)
        data = {
            'question_id': question.question_id,
            'exam_id': question.exam_id,
            'question_text': question.question_text,
            'question_type': question.question_type,
            'marks': question.marks,
            'question_order': question.question_order,
            'is_required': question.is_required,
            'expected_answer': question.expected_answer,
            'marking_scheme': question.marking_scheme,
            'options': [
                {
                    'option_text': o.option_text,
                    'is_correct': o.is_correct,
                    'explanation': o.explanation,
                    'option_order': o.option_order,
                } for o in options
            ],
        }
        return Response(data)

    def put(self, request, question_id: str):
        question = QuestionSelector.get_question(question_id)
        serializer = QuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        question = QuestionService.update_question_new(
            question=question,
            question_text=validated['question_text'],
            marks=float(validated['marks']),
            is_required=validated['is_required'],
            expected_answer=validated.get('expected_answer', ''),
            marking_scheme=validated.get('marking_scheme', ''),
            options=validated['options'],
        )
        return Response({'question_id': question.question_id})

    def delete(self, request, question_id: str):
        question = QuestionSelector.get_question(question_id)
        QuestionService.delete_question(question)
        return Response(status=status.HTTP_204_NO_CONTENT)
