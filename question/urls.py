from django.urls import path, include
from .views import category, question_bank, question

app_name = 'question'

# Question Bank Category URLs
category_patterns = [
    path('', category.QuestionBankCategoryListView.as_view(), name='category-list'),
    path('create/', category.QuestionBankCategoryCreateView.as_view(), name='category-create'),
    path('<int:category_id>/', category.QuestionBankCategoryDetailView.as_view(), name='category-detail'),
    path('<int:category_id>/update/', category.QuestionBankCategoryUpdateView.as_view(), name='category-update'),
    path('<int:category_id>/delete/', category.QuestionBankCategoryDeleteView.as_view(), name='category-delete'),
]

# Question Bank URLs
bank_patterns = [
    path('', question_bank.QuestionBankListView.as_view(), name='bank-list'),
    path('create/', question_bank.QuestionBankCreateView.as_view(), name='bank-create'),
    path('<int:question_id>/', question_bank.QuestionBankDetailView.as_view(), name='bank-detail'),
    path('<int:question_id>/update/', question_bank.QuestionBankUpdateView.as_view(), name='bank-update'),
    path('<int:question_id>/approve/', question_bank.QuestionBankApproveView.as_view(), name='bank-approve'),
    path('<int:question_id>/duplicate/', question_bank.QuestionBankDuplicateView.as_view(), name='bank-duplicate'),
]

# Exam Question URLs
exam_patterns = [
    path('<int:exam_id>/questions/', question.ExamQuestionListView.as_view(), name='exam-question-list'),
    path('<int:exam_id>/questions/create-from-bank/', question.ExamQuestionCreateFromBankView.as_view(), name='exam-question-create-from-bank'),
    path('<int:exam_id>/questions/create-custom/', question.ExamQuestionCreateCustomView.as_view(), name='exam-question-create-custom'),
    path('<int:exam_id>/questions/reorder/', question.ExamQuestionReorderView.as_view(), name='exam-question-reorder'),
    path('questions/<int:question_id>/', question.ExamQuestionDetailView.as_view(), name='exam-question-detail'),
    path('questions/<int:question_id>/update/', question.ExamQuestionUpdateView.as_view(), name='exam-question-update'),
    path('questions/<int:question_id>/delete/', question.ExamQuestionDeleteView.as_view(), name='exam-question-delete'),
]

urlpatterns = [
    # Question Bank Category routes
    path('categories/', include(category_patterns)),
    
    # Question Bank routes
    path('bank/', include(bank_patterns)),
    
    # Exam Question routes
    path('exam/', include(exam_patterns)),
]