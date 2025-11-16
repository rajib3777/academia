from django.urls import path

from exam.apis import exam_apis

app_name = 'exam'

urlpatterns = [
    # Exam Management
    path('exams/', exam_apis.ExamListAPI.as_view(), name='exam-list'),
    path('exams/create/', exam_apis.ExamCreateAPI.as_view(), name='exam-create'),
    path('exams/<str:exam_id>/', exam_apis.ExamDetailView.as_view(), name='exam-detail'),
    path('exams/<str:exam_id>/update/', exam_apis.ExamUpdateView.as_view(), name='exam-update'),
    path('exams/<str:exam_id>/delete/', exam_apis.ExamDeleteView.as_view(), name='exam-delete'),

    path('exams/<str:exam_id>/publish/', exam_apis.ExamPublishView.as_view(), name='exam-publish'),
    path('exams/<str:exam_id>/publish-results/', exam_apis.ExamResultsPublishView.as_view(), name='exam-publish-results'),
    path('exams/<str:exam_id>/analytics/', exam_apis.ExamAnalyticsView.as_view(), name='exam-analytics'),
    path('exams/<str:exam_id>/students/', exam_apis.ExamStudentsView.as_view(), name='exam-students'),

    # Exam Results
    path('exam-results/', exam_apis.ExamResultListView.as_view(), name='exam-result-list'),
    path('exam-results/create/', exam_apis.ExamResultCreateView.as_view(), name='exam-result-create'),
    path('exam-results/<str:result_id>/', exam_apis.ExamResultDetailView.as_view(), name='exam-result-detail'),
    path('exam-results/<str:result_id>/update/', exam_apis.ExamResultUpdateView.as_view(), name='exam-result-update'),
    path('exam-results/<str:result_id>/verify/', exam_apis.ExamResultVerifyView.as_view(), name='exam-result-verify'),

    # Batch Operations
    path('exams/<str:exam_id>/batch-results/', exam_apis.BatchExamResultsView.as_view(), name='exam-batch-results'),
    path('exams/<str:exam_id>/export/', exam_apis.ExamResultsExportView.as_view(), name='exam-results-export'),

    # Online Exam Sessions
    path('exam-sessions/', exam_apis.StudentExamSessionListView.as_view(), name='exam-session-list'),
    path('exam-sessions/<str:session_id>/', exam_apis.StudentExamSessionDetailView.as_view(), name='exam-session-detail'),
    path('exams/<str:exam_id>/start-session/', exam_apis.StartExamSessionView.as_view(), name='start-exam-session'),
    path('exam-sessions/<str:session_id>/submit/', exam_apis.SubmitExamSessionView.as_view(), name='submit-exam-session'),
    path('exam-sessions/<str:session_id>/status/', exam_apis.ExamSessionStatusView.as_view(), name='exam-session-status'),
    path('exam-sessions/<str:session_id>/extend-time/', exam_apis.ExtendExamTimeView.as_view(), name='extend-exam-time'),

    # Student Answers
    path('exam-sessions/<str:session_id>/answers/', exam_apis.StudentAnswerListAPI.as_view(), name='student-answer-list'),
    path('exam-sessions/<str:session_id>/answers/create/', exam_apis.StudentAnswerCreateAPI.as_view(), name='student-answer-create'),
    path('student-answers/<int:answer_id>/grade/', exam_apis.GradeStudentAnswerView.as_view(), name='grade-student-answer'),

    # Online Exam Results
    path('online-exam-results/', exam_apis.OnlineExamResultListView.as_view(), name='online-exam-result-list'),
    path('online-exam-results/<str:result_id>/', exam_apis.OnlineExamResultDetailView.as_view(), name='online-exam-result-detail'),
    path('exam-sessions/<str:session_id>/process-result/', exam_apis.ProcessOnlineExamResultView.as_view(), name='process-online-exam-result'),
    path('online-exam-results/<str:result_id>/complete-grading/', exam_apis.CompleteManualGradingView.as_view(), name='complete-manual-grading'),
    
    # Student History
    path('students/<int:student_id>/exam-history/', exam_apis.StudentExamHistoryView.as_view(), name='student-exam-history'),
]