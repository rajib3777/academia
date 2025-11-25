from django.urls import path, include
from question.apis import question_apis

app_name = 'question'

# Question Bank Category URLs
category_patterns = [
    path('question-bank/categories/', question_apis.QuestionBankCategoryListView.as_view(), name='category-list'),
    path('question-bank/categories/create/', question_apis.QuestionBankCategoryCreateView.as_view(), name='category-create'),
    path('question-bank/categories/<int:category_id>/', question_apis.QuestionBankCategoryDetailView.as_view(), name='category-detail'),
    path('question-bank/categories/<int:category_id>/update/', question_apis.QuestionBankCategoryUpdateView.as_view(), name='category-update'),
    path('question-bank/categories/<int:category_id>/delete/', question_apis.QuestionBankCategoryDeleteView.as_view(), name='category-delete'),
]

# Question Bank URLs
bank_patterns = [
    path('question-bank/', question_apis.QuestionBankListView.as_view(), name='bank-list'),
    path('question-bank/create/', question_apis.QuestionBankCreateView.as_view(), name='bank-create'),
    path('question-bank/<int:question_id>/', question_apis.QuestionBankDetailView.as_view(), name='bank-detail'),
    path('question-bank/<int:question_id>/update/', question_apis.QuestionBankUpdateView.as_view(), name='bank-update'),
    path('question-bank/<int:question_id>/approve/', question_apis.QuestionBankApproveView.as_view(), name='bank-approve'),
    path('question-bank/<int:question_id>/duplicate/', question_apis.QuestionBankDuplicateView.as_view(), name='bank-duplicate'),
]

# Exam Question URLs
exam_patterns = [
    path('exam/<int:exam_id>/questions/', question_apis.ExamQuestionListView.as_view(), name='exam-question-list'),
    path('exam/<int:exam_id>/questions/create-from-bank/', question_apis.ExamQuestionCreateFromBankView.as_view(), name='exam-question-create-from-bank'),
    path('exam/<int:exam_id>/questions/create-custom/', question_apis.ExamQuestionCreateCustomView.as_view(), name='exam-question-create-custom'),
    path('exam/<int:exam_id>/questions/reorder/', question_apis.ExamQuestionReorderView.as_view(), name='exam-question-reorder'),
    path('exam/questions/<int:question_id>/', question_apis.ExamQuestionDetailView.as_view(), name='exam-question-detail'),
    path('exam/questions/<int:question_id>/update/', question_apis.ExamQuestionUpdateView.as_view(), name='exam-question-update'),
    path('exam/questions/<int:question_id>/delete/', question_apis.ExamQuestionDeleteView.as_view(), name='exam-question-delete'),
]

question_patterns = [
    # path('questions/', question_apis.QuestionListCreateAPI.as_view(), name='question-list-create'),
    # path('questions/<str:question_id>/', question_apis.QuestionDetailUpdateDeleteAPI.as_view(), name='question-detail-update-delete'),
]

urlpatterns = category_patterns + bank_patterns + exam_patterns + question_patterns