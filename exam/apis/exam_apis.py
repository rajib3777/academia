from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.paginator import Paginator
from student.serializers import student_serializers
from functools import cached_property
from classmate.permissions import AuthenticatedGenericView
from exam.selectors import exam_selector
from exam.services import exam_service
from exam.serializers import exam_serializer


class ExamCreateAPI(AuthenticatedGenericView, APIView):
    """List and create exams"""
    serializer_class = exam_serializer.ExamSerializer

    @cached_property
    def exam_service(self) -> exam_service.ExamService:
        """Lazy initialization of ExamService."""
        return exam_service.ExamService()

    def post(self, request):
        """Create a new exam"""
        serializer = exam_serializer.ExamCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                exam = self.exam_service.create_exam(
                    data=serializer.validated_data,
                    user=request.user
                )
                response_serializer = self.serializer_class(exam)
                return Response({'success': True, 'data': response_serializer.data}, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExamListAPI(AuthenticatedGenericView, APIView):
    """List and create exams"""
    serializer_class = exam_serializer.ExamSerializer
    
    @cached_property
    def exam_selector(self) -> exam_selector.ExamSelector:
        """Lazy initialization of ExamSelector."""
        return exam_selector.ExamSelector()

    def get(self, request):
        try:
            """List exams with pagination and filters"""
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
            search_query = request.GET.get('search', '').strip()
            ordering = request.GET.get('ordering')

            pagination_info = self.exam_selector.list_exams(
                request_user=request.user,
                filters=request.GET,
                search_query=search_query,
                ordering=ordering,
                page=page,
                page_size=page_size,
            )

            # Serialize data
            serializer = self.serializer_class(pagination_info['results'], many=True)

            # Build response
            response_data = {
                'success': True,
                'data': serializer.data,
                'pagination': pagination_info['pagination'],
                'filters_applied': dict(request.GET),
                'total_count': pagination_info['pagination']['total_items']
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            # Log the exception
            import logging
            logger = logging.getLogger(__name__)
            logger.exception("Error in ExamListAPI GET: %s", str(e))
            
            return Response(
                {
                    'success': False,
                    'error': 'Failed to retrieve exams',
                    'details': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

class ExamDetailView(AuthenticatedGenericView, APIView):
    """Retrieve, update, and delete exam"""
    serializer_class = exam_serializer.ExamSerializer

    @cached_property
    def exam_selector(self) -> exam_selector.ExamSelector:
        """Lazy initialization of ExamSelector."""
        return exam_selector.ExamSelector()

    def get(self, request, exam_id):
        """Get exam details with statistics"""
        exam = self.exam_selector.get_exam_queryset(exam_id)
        if not exam:
            return Response(
                {'error': 'Exam not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.serializer_class(exam)
        return Response(serializer.data)


class ExamUpdateView(AuthenticatedGenericView, APIView):
    """Retrieve, update, and delete exam"""
    serializer_class = exam_serializer.ExamSerializer

    @cached_property
    def exam_service(self) -> exam_service.ExamService:
        """Lazy initialization of ExamService."""
        return exam_service.ExamService()

    def put(self, request, exam_id):
        """Update exam"""
        serializer = exam_serializer.ExamUpdateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                exam = self.exam_service.update_exam(
                    exam_id=exam_id,
                    data=serializer.validated_data,
                    user=request.user
                )
                response_serializer = self.serializer_class(exam)
                return Response(response_serializer.data)
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExamDeleteView(AuthenticatedGenericView, APIView):
    """Retrieve, update, and delete exam"""
    permission_classes = [IsAuthenticated]

    @cached_property
    def exam_service(self) -> exam_service.ExamService:
        """Lazy initialization of ExamService."""
        return exam_service.ExamService()

    def delete(self, request, exam_id):
        """Delete exam"""
        try:
            self.exam_service.delete_exam(exam_id=exam_id, user=request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ExamPublishView(AuthenticatedGenericView, APIView):
    """Publish exam"""
    serializer_class = exam_serializer.ExamSerializer

    @cached_property
    def exam_service(self) -> exam_service.ExamService:
        """Lazy initialization of ExamService."""
        return exam_service.ExamService()

    def post(self, request, exam_id):
        """Publish an exam"""
        try:
            exam = self.exam_service.publish_exam(exam_id=exam_id, user=request.user)
            serializer = self.serializer_class(exam)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ExamResultsPublishView(AuthenticatedGenericView, APIView):
    """Publish exam results"""
    serializer_class = exam_serializer.ExamSerializer

    @cached_property
    def exam_service(self) -> exam_service.ExamService:
        """Lazy initialization of ExamService."""
        return exam_service.ExamService()

    def post(self, request, exam_id):
        """Publish exam results"""
        try:
            exam = self.exam_service.publish_results(exam_id=exam_id, user=request.user)
            serializer = self.serializer_class(exam)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ExamAnalyticsView(AuthenticatedGenericView, APIView):
    """Get exam analytics"""
    serializer_class = exam_serializer.ExamAnalyticsSerializer
    
    @cached_property
    def exam_result_selector(self) -> exam_selector.ExamResultSelector:
        """Lazy initialization of ExamResultSelector."""
        return exam_selector.ExamResultSelector()
    
    def get(self, request, exam_id):
        """Get exam result analytics"""
        analytics = self.exam_result_selector.get_exam_result_analytics(exam_id)
        serializer = self.serializer_class(analytics)
        return Response(serializer.data)


class ExamResultListView(AuthenticatedGenericView, APIView):
    """List and create exam results"""
    serializer_class = exam_serializer.ExamResultSerializer
    
    @cached_property
    def exam_result_selector(self) -> exam_selector.ExamResultSelector:
        """Lazy initialization of ExamResultSelector."""
        return exam_selector.ExamResultSelector()
    
    def get(self, request):
        """List exam results with pagination and filters"""
        page_number = request.GET.get('page', 1)
        exam_id = request.GET.get('exam_id')
        student_id = request.GET.get('student_id')
        batch_id = request.GET.get('batch_id')
        is_passed = request.GET.get('is_passed')

        # Convert string to boolean for is_passed
        if is_passed:
            is_passed = is_passed.lower() == 'true'

        results = self.exam_result_selector.list_exam_results(
            exam_id=exam_id,
            student_id=student_id,
            batch_id=batch_id,
            is_passed=is_passed
        )

        # Pagination
        paginator = Paginator(results, 10)
        page = paginator.get_page(page_number)

        serializer = self.serializer_class(page.object_list, many=True)
        return Response({
            'results': serializer.data,
            'pagination': {
                'current_page': page.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page.has_next(),
                'has_previous': page.has_previous()
            }
        })


class ExamResultCreateView(AuthenticatedGenericView, APIView):
    """List and create exam results"""
    serializer_class = exam_serializer.ExamResultSerializer

    @cached_property
    def exam_result_service(self) -> exam_service.ExamResultService:
        """Lazy initialization of ExamResultService."""
        return exam_service.ExamResultService()

    def post(self, request):
        """Create exam result"""
        serializer = exam_serializer.ExamResultCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                result = self.exam_result_service.create_result(
                    data=serializer.validated_data,
                    user=request.user
                )
                response_serializer = self.serializer_class(result)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExamResultUpdateView(AuthenticatedGenericView, APIView):
    """Retrieve, update exam result"""
    serializer_class = exam_serializer.ExamResultSerializer

    @cached_property
    def exam_result_service(self) -> exam_service.ExamResultService:
        """Lazy initialization of ExamResultService."""
        return exam_service.ExamResultService()

    def put(self, request, result_id):
        """Update exam result"""
        try:
            result = self.exam_result_service.update_result(
                result_id=result_id,
                data=request.data,
                user=request.user
            )
            serializer = self.serializer_class(result)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        

class ExamResultDetailView(AuthenticatedGenericView, APIView):
    """Retrieve, update exam result"""
    serializer_class = exam_serializer.ExamResultSerializer
    
    @cached_property
    def exam_result_selector(self) -> exam_selector.ExamResultSelector:
        """Lazy initialization of ExamResultSelector."""
        return exam_selector.ExamResultSelector()
    
    def get(self, request, result_id):
        """Get exam result details"""
        result = self.exam_result_selector.get_result_by_id(result_id)
        if not result:
            return Response(
                {'error': 'Result not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.serializer_class(result)
        return Response(serializer.data)


class StudentExamSessionListView(AuthenticatedGenericView, APIView):
    """List student exam sessions"""
    serializer_class = exam_serializer.StudentExamSessionSerializer
    
    @cached_property
    def student_exam_session_selector(self) -> exam_selector.StudentExamSessionSelector:
        """Lazy initialization of StudentExamSessionSelector."""
        return exam_selector.StudentExamSessionSelector()
    
    def get(self, request):
        """List exam sessions with filters"""
        exam_id = request.GET.get('exam_id')
        student_id = request.GET.get('student_id')
        session_status = request.GET.get('status')

        sessions = self.student_exam_session_selector.list_exam_sessions(
            exam_id=exam_id,
            student_id=student_id,
            status=session_status
        )

        serializer = self.serializer_class(sessions, many=True)
        return Response(serializer.data)


class StudentExamSessionDetailView(AuthenticatedGenericView, APIView):
    """Student exam session details and operations"""
    serializer_class = exam_serializer.StudentExamSessionSerializer
    
    @cached_property
    def student_exam_session_selector(self) -> exam_selector.StudentExamSessionSelector:
        """Lazy initialization of StudentExamSessionSelector."""
        return exam_selector.StudentExamSessionSelector()
    
    def get(self, request, session_id):
        """Get session details"""
        session = self.student_exam_session_selector.get_session_by_id(session_id)
        if not session:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.serializer_class(session)
        return Response(serializer.data)


class StartExamSessionView(AuthenticatedGenericView, APIView):
    """Start exam session for online exams"""
    serializer_class = exam_serializer.StudentExamSessionSerializer

    @cached_property
    def student_exam_session_service(self) -> exam_service.StudentExamSessionService:
        """Lazy initialization of StudentExamSessionService."""
        return exam_service.StudentExamSessionService()

    def post(self, request, exam_id):
        """Start exam session"""
        try:
            # Get IP address and user agent
            ip_address = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Assume student_id is from authenticated user or passed in request
            student_id = request.data.get('student_id') or getattr(request.user, 'student_profile', {}).get('id')
            
            session = self.student_exam_session_service.start_exam_session(
                exam_id=exam_id,
                student_id=student_id,
                ip_address=ip_address,
                user_agent=user_agent
            )

            serializer = self.serializer_class(session)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SubmitExamSessionView(AuthenticatedGenericView, APIView):
    """Submit exam session"""
    serializer_class = exam_serializer.StudentExamSessionSerializer

    @cached_property
    def student_exam_session_service(self) -> exam_service.StudentExamSessionService:
        """Lazy initialization of StudentExamSessionService."""
        return exam_service.StudentExamSessionService()
    
    def post(self, request, session_id):
        """Submit exam session"""
        try:
            session = self.student_exam_session_service.submit_exam_session(session_id)
            serializer = self.serializer_class(session)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class StudentAnswerListAPI(AuthenticatedGenericView, APIView):
    """List and create student answers"""
    
    @cached_property
    def student_answer_selector(self) -> exam_selector.StudentAnswerSelector:
        """Lazy initialization of StudentAnswerSelector."""
        return exam_selector.StudentAnswerSelector()
    
    def get(self, request, session_id):
        """Get all answers for a session"""
        answers = self.student_answer_selector.list_session_answers(session_id)
        serializer = exam_serializer.StudentAnswerSerializer(answers, many=True)
        return Response(serializer.data)


class StudentAnswerCreateAPI(AuthenticatedGenericView, APIView):
    """List and create student answers"""
    @cached_property
    def student_answer_service(self) -> exam_service.StudentAnswerService:
        """Lazy initialization of StudentAnswerService."""
        return exam_service.StudentAnswerService()

    def post(self, request, session_id):
        """Save student answer"""
        serializer = exam_serializer.StudentAnswerCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                answer = self.student_answer_service.save_answer(
                    session_id=session_id,
                    question_id=serializer.validated_data['question_id'],
                    answer_data={
                        'selected_option_id': serializer.validated_data.get('selected_option_id'),
                        'text_answer': serializer.validated_data.get('text_answer', '')
                    }
                )
                response_serializer = exam_serializer.StudentAnswerSerializer(answer)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GradeStudentAnswerView(AuthenticatedGenericView, APIView):
    """Grade student answer manually"""

    @cached_property
    def student_answer_service(self) -> exam_service.StudentAnswerService:
        """Lazy initialization of StudentAnswerService."""
        return exam_service.StudentAnswerService()

    def post(self, request, answer_id):
        """Grade an answer manually"""
        serializer = exam_serializer.StudentAnswerGradeSerializer(data=request.data)
        if serializer.is_valid():
            try:
                answer = self.student_answer_service.grade_answer(
                    answer_id=answer_id,
                    awarded_marks=serializer.validated_data['awarded_marks'],
                    grader_remarks=serializer.validated_data.get('grader_remarks', ''),
                    graded_by=request.user
                )
                response_serializer = exam_serializer.StudentAnswerSerializer(answer)
                return Response(response_serializer.data)
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OnlineExamResultListView(AuthenticatedGenericView, APIView):
    """List online exam results"""
    serializer_class = exam_serializer.OnlineExamResultSerializer
    
    @cached_property
    def online_exam_result_selector(self) -> exam_selector.OnlineExamResultSelector:
        """Lazy initialization of OnlineExamResultSelector."""
        return exam_selector.OnlineExamResultSelector()
    
    def get(self, request):
        """List online exam results with filters"""
        page_number = request.GET.get('page', 1)
        exam_id = request.GET.get('exam_id')
        student_id = request.GET.get('student_id')
        requires_grading = request.GET.get('requires_grading')

        # Convert string to boolean
        if requires_grading:
            requires_grading = requires_grading.lower() == 'true'

        results = self.online_exam_result_selector.list_online_exam_results(
            exam_id=exam_id,
            student_id=student_id,
            requires_manual_grading=requires_grading
        )

        # Pagination
        paginator = Paginator(results, 10)
        page = paginator.get_page(page_number)


        serializer = self.serializer_class(page.object_list, many=True)
        return Response({
            'results': serializer.data,
            'pagination': {
                'current_page': page.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page.has_next(),
                'has_previous': page.has_previous()
            }
        })


class OnlineExamResultDetailView(AuthenticatedGenericView, APIView):
    """Online exam result details"""
    serializer_class = exam_serializer.OnlineExamResultSerializer
    
    @cached_property
    def online_exam_result_selector(self) -> exam_selector.OnlineExamResultSelector:
        """Lazy initialization of OnlineExamResultSelector."""
        return exam_selector.OnlineExamResultSelector()
    
    def get(self, request, result_id):
        """Get online exam result with session details"""
        result = self.online_exam_result_selector.get_online_result_by_session(result_id)
        if not result:
            return Response(
                {'error': 'Result not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.serializer_class(result)
        return Response(serializer.data)


class ProcessOnlineExamResultView(AuthenticatedGenericView, APIView):
    """Process online exam result"""
    serializer_class = exam_serializer.OnlineExamResultSerializer

    @cached_property
    def online_exam_result_service(self) -> exam_service.OnlineExamResultService:
        """Lazy initialization of OnlineExamResultService."""
        return exam_service.OnlineExamResultService()

    def post(self, request, session_id):
        """Process online exam result after submission"""
        try:
            result = self.online_exam_result_service.process_exam_result(session_id)
            serializer = self.serializer_class(result)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class CompleteManualGradingView(AuthenticatedGenericView, APIView):
    """Complete manual grading for online exam"""
    serializer_class = exam_serializer.OnlineExamResultSerializer

    @cached_property
    def online_exam_result_service(self) -> exam_service.OnlineExamResultService:
        """Lazy initialization of OnlineExamResultService."""
        return exam_service.OnlineExamResultService()
    
    def post(self, request, result_id):
        """Mark manual grading as complete"""
        try:
            result = self.online_exam_result_service.complete_manual_grading(
                result_id=result_id,
                user=request.user
            )
            serializer = self.serializer_class(result)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class BatchExamResultsView(AuthenticatedGenericView, APIView):
    """Batch operations for exam results"""
    serializer_class = exam_serializer.ExamResultSerializer

    @cached_property
    def exam_result_service(self) -> exam_service.ExamResultService:
        """Lazy initialization of ExamResultService."""
        return exam_service.ExamResultService()
    
    def post(self, request, exam_id):
        """Create multiple exam results at once"""
        try:
            results_data = request.data.get('results', [])
            results = self.exam_result_service.bulk_create_results(
                exam_id=exam_id,
                results_data=results_data,
                user=request.user
            )
            serializer = self.serializer_class(results, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ExamStudentsView(AuthenticatedGenericView, APIView):
    """Get students enrolled in exam batch"""
    serializer_class = student_serializers.StudentSerializer
    
    @cached_property
    def exam_selector(self) -> exam_selector.ExamSelector:
        """Lazy initialization of ExamSelector."""
        return exam_selector.ExamSelector()
    
    def get(self, request, exam_id):
        """Get list of students for an exam"""
        try:
            # Extract pagination parameters
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
            
            # Extract search and ordering parameters
            search_query = request.GET.get('search', '').strip()
            ordering = request.GET.get('ordering')

            pagination_info = self.exam_selector.list_exams_student(
                exam_id=exam_id,
                filters=request.GET,
                search_query=search_query,
                ordering=ordering,
                page=page,
                page_size=page_size
            )

            # Serialize data
            serializer = self.serializer_class(pagination_info['results'], many=True)

            # Build response
            response_data = {
                'success': True,
                'data': serializer.data,
                'pagination': pagination_info['pagination'],
                'filters_applied': dict(request.GET),
                'total_count': pagination_info['pagination']['total_items']
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            # Log the exception
            import logging
            logger = logging.getLogger(__name__)
            logger.exception("Error in ExamStudentListView")
            
            return Response(
                {
                    'success': False,
                    'error': 'Failed to retrieve exam students',
                    'details': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

class ExamSessionStatusView(AuthenticatedGenericView, APIView):
    """Update exam session status"""
    serializer_class = exam_serializer.StudentExamSessionSerializer

    @cached_property
    def student_exam_session_service(self) -> exam_service.StudentExamSessionService:
        """Lazy initialization of StudentExamSessionService."""
        return exam_service.StudentExamSessionService()
    
    def patch(self, request, session_id):
        """Update session status (timeout, interrupted, etc.)"""
        status_value = request.data.get('status')
        time_spent = request.data.get('time_spent_minutes')
        
        try:
            session = self.student_exam_session_service.update_session_status(
                session_id=session_id,
                status=status_value,
                time_spent_minutes=time_spent
            )
            serializer = self.serializer_class(session)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ExtendExamTimeView(AuthenticatedGenericView, APIView):
    """Extend exam time for a session"""
    serializer_class = exam_serializer.StudentExamSessionSerializer

    @cached_property
    def student_exam_session_service(self) -> exam_service.StudentExamSessionService:
        """Lazy initialization of StudentExamSessionService."""
        return exam_service.StudentExamSessionService()
    
    def post(self, request, session_id):
        """Extend exam time"""
        extended_minutes = request.data.get('extended_time_minutes', 0)
        
        try:
            session = self.student_exam_session_service.extend_exam_session_time(
                session_id=session_id,
                extended_minutes=extended_minutes,
                extended_by=request.user
            )
            serializer = self.serializer_class(session)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ExamResultsExportView(AuthenticatedGenericView, APIView):
    """Export exam results"""

    @cached_property
    def exam_result_service(self) -> exam_service.ExamResultService:
        """Lazy initialization of ExamResultService."""
        return exam_service.ExamResultService()

    def get(self, request, exam_id):
        """Export exam results to CSV/Excel"""
        export_format = request.GET.get('format', 'csv')
        
        try:
            if export_format == 'csv':
                response = self.exam_result_service.export_results_csv(exam_id)
            elif export_format == 'excel':
                response = self.exam_result_service.export_results_excel(exam_id)
            else:
                return Response(
                    {'error': 'Invalid format. Use csv or excel'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return response
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class StudentExamHistoryView(AuthenticatedGenericView, APIView):
    """Get student exam history"""
    serializer_class = exam_serializer.ExamResultSerializer

    @cached_property
    def exam_result_selector(self) -> exam_selector.ExamResultSelector:
        """Lazy initialization of ExamResultSelector."""
        return exam_selector.ExamResultSelector()
    
    def get(self, request, student_id):
        """Get exam history for a student"""
        results = self.exam_result_selector.get_student_exam_history(student_id)
        serializer = self.serializer_class(results, many=True)
        return Response(serializer.data)


class ExamResultVerifyView(AuthenticatedGenericView, APIView):
    """Verify exam results"""
    serializer_class = exam_serializer.ExamResultSerializer

    @cached_property
    def exam_result_service(self) -> exam_service.ExamResultService:
        """Lazy initialization of ExamResultService."""
        return exam_service.ExamResultService()
    
    def post(self, request, result_id):
        """Verify an exam result"""
        try:
            result = self.exam_result_service.verify_result(
                result_id=result_id,
                verified_by=request.user
            )
            serializer = self.serializer_class(result)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def delete(self, request, result_id):
        """Unverify an exam result"""
        try:
            result = self.exam_result_service.unverify_result(result_id)
            serializer = self.serializer_class(result)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )