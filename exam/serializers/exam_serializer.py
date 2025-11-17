from rest_framework import serializers
from django.utils import timezone
from exam.choices import EXAM_TYPE_CHOICES
from exam.models import (
    Exam
)


class GradeSerializer(serializers.Serializer):
    """Grade serializer"""
    id = serializers.IntegerField(read_only=True)
    grade = serializers.CharField()

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'grade': instance.grade,
            'display_name': instance.get_grade_display()
        }


class ExamSerializer(serializers.Serializer):
    """Exam serializer"""
    id = serializers.IntegerField(read_only=True)
    exam_id = serializers.CharField(read_only=True)
    title = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    subject = serializers.CharField()
    exam_date = serializers.DateTimeField()
    duration_minutes = serializers.IntegerField()
    total_marks = serializers.DecimalField(max_digits=6, decimal_places=2)
    pass_marks = serializers.DecimalField(max_digits=6, decimal_places=2)
    exam_type = serializers.CharField()
    is_published = serializers.BooleanField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    results_published = serializers.BooleanField(read_only=True)
    result_published_at = serializers.DateTimeField(read_only=True)
    
    # Write-only fields for creation
    batch_id = serializers.IntegerField(write_only=True)

    # Computed fields
    is_completed = serializers.BooleanField()
    can_publish_results = serializers.BooleanField()
    enrolled_students_count = serializers.IntegerField()
    results_submitted_count = serializers.IntegerField()
    pending_results_count = serializers.IntegerField()

    def to_representation(self, instance):
        data = {
            'id': instance.id,
            'exam_id': instance.exam_id,
            'title': instance.title,
            'description': instance.description,
            'subject': instance.subject,
            'subject_display': instance.get_subject_display(),
            'exam_date': instance.exam_date,
            'duration_minutes': instance.duration_minutes,
            'total_marks': str(instance.total_marks),
            'pass_marks': str(instance.pass_marks),
            'exam_type': instance.exam_type,
            'exam_type_display': instance.get_exam_type_display(),
            'is_published': instance.is_published,
            'is_active': instance.is_active,
            'results_published': instance.results_published,
            'result_published_at': instance.result_published_at,
            'is_completed': instance.is_completed,
            'can_publish_results': instance.can_publish_results,
            'enrolled_students_count': instance.enrolled_students_count,
            'results_submitted_count': instance.results_submitted_count,
            'pending_results_count': instance.pending_results_count,
            'batch': {
                'id': instance.batch.id,
                'name': instance.batch.name,
                'course': {
                    'name': instance.batch.course.name,
                    'academy': {
                        'name': instance.batch.course.academy.name
                    }
                }
            },
            'published_by': {
                'id': instance.published_by.id,
                'name': instance.published_by.get_full_name()
            } if instance.published_by else None,
            'created_at': instance.created_at,
            'modified_at': instance.modified_at,
            # Include stats if available
            'stats': {
                'results_count': getattr(instance, 'results_count', 0),
                'avg_marks': getattr(instance, 'avg_marks', 0),
                'max_marks': getattr(instance, 'max_marks', 0),
                'min_marks': getattr(instance, 'min_marks', 0),
                'pass_count': getattr(instance, 'pass_count', 0),
                'fail_count': getattr(instance, 'fail_count', 0),
                'pass_percentage': round(getattr(instance, 'pass_percentage', 0) or 0, 2),
                'grade_a_plus_count': getattr(instance, 'grade_a_plus_count', 0),
                'grade_a_count': getattr(instance, 'grade_a_count', 0),
                'grade_a_minus_count': getattr(instance, 'grade_a_minus_count', 0),
                'grade_b_count': getattr(instance, 'grade_b_count', 0),
                'grade_c_count': getattr(instance, 'grade_c_count', 0),
                'grade_d_count': getattr(instance, 'grade_d_count', 0),
                'grade_f_count': getattr(instance, 'grade_f_count', 0),
                'present_count': getattr(instance, 'present_count', 0),
                'absent_count': getattr(instance, 'absent_count', 0),
            }
        }

        # Add batch info if available
        if hasattr(instance, 'batch') and instance.batch:
            data['batch'] = {
                'id': instance.batch.id,
                'name': instance.batch.name,
                'batch_id': instance.batch.batch_id,
                'course': {
                    'id': instance.batch.course.id,
                    'name': instance.batch.course.name,
                    'subject': instance.batch.course.subject
                } if instance.batch.course else None
            }

        # Add publisher info if available
        if hasattr(instance, 'published_by') and instance.published_by:
            data['published_by'] = {
                'id': instance.published_by.id,
                'username': instance.published_by.username,
                'full_name': instance.published_by.get_full_name()
            }

        # Add statistics if available (from annotations)
        if hasattr(instance, 'total_results'):
            data['statistics'] = {
                'total_results': instance.total_results,
                'avg_marks': str(instance.avg_marks) if instance.avg_marks else '0.00',
                'pass_count': instance.pass_count,
                'pass_percentage': round(
                    (instance.pass_count / instance.total_results * 100) 
                    if instance.total_results > 0 else 0, 2
                )
            }

        return data

    def validate(self, data):
        """Validate exam data"""
        if data.get('pass_marks') and data.get('total_marks'):
            if data['pass_marks'] > data['total_marks']:
                raise serializers.ValidationError(
                    'Pass marks cannot be greater than total marks'
                )
        
        if not self.instance and data.get('exam_date'):
            if data['exam_date'] < timezone.now():
                raise serializers.ValidationError(
                    'Exam date cannot be in the past'
                )
        
        return data


class ExamResultSerializer(serializers.Serializer):
    """Exam result serializer"""
    id = serializers.IntegerField(read_only=True)
    result_id = serializers.CharField(read_only=True)
    obtained_marks = serializers.DecimalField(max_digits=6, decimal_places=2)
    is_passed = serializers.BooleanField(read_only=True)
    was_present = serializers.BooleanField(default=True)
    remarks = serializers.CharField(required=False, allow_blank=True)
    is_verified = serializers.BooleanField(read_only=True)
    
    # Write-only fields for creation
    exam_id = serializers.CharField(write_only=True, required=False)
    student_id = serializers.IntegerField(write_only=True, required=False)
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    status = serializers.CharField()

    def to_representation(self, instance):
        data = {
            'id': instance.id,
            'result_id': instance.result_id,
            'obtained_marks': str(instance.obtained_marks),
            'is_passed': instance.is_passed,
            'was_present': instance.was_present,
            'remarks': instance.remarks,
            'is_verified': instance.is_verified,
            'percentage': instance.percentage,
            'status': instance.status,
            'entered_at': instance.entered_at,
            'last_modified_at': instance.last_modified_at
        }

        # Add exam info
        if hasattr(instance, 'exam') and instance.exam:
            data['exam'] = {
                'id': instance.exam.id,
                'exam_id': instance.exam.exam_id,
                'title': instance.exam.title,
                'subject': instance.exam.subject,
                'total_marks': str(instance.exam.total_marks),
                'pass_marks': str(instance.exam.pass_marks),
                'exam_date': instance.exam.exam_date
            }

        # Add student info
        if hasattr(instance, 'student') and instance.student:
            data['student'] = {
                'id': instance.student.id,
                'student_id': instance.student.student_id,
                'user': {
                    'id': instance.student.user.id,
                    'username': instance.student.user.username,
                    'first_name': instance.student.user.first_name,
                    'last_name': instance.student.user.last_name,
                    'full_name': instance.student.user.get_full_name()
                } if instance.student.user else None
            }

        # Add grade info
        if hasattr(instance, 'grade') and instance.grade:
            data['grade'] = {
                'id': instance.grade.id,
                'grade': instance.grade.grade
            }

        # Add entry tracking
        if hasattr(instance, 'entered_by') and instance.entered_by:
            data['entered_by'] = {
                'id': instance.entered_by.id,
                'username': instance.entered_by.username,
                'full_name': instance.entered_by.get_full_name()
            }

        return data


class ExamResultBulkCreateSerializer(serializers.Serializer):
    """Serializer for bulk creating exam results for all students in a batch"""
    
    # Default values to apply to all results
    default_obtained_marks = serializers.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        required=False, 
        default=0,
        help_text="Default marks to assign to all students (can be updated later)"
    )
    default_was_present = serializers.BooleanField(
        default=True,
        help_text="Default attendance status for all students"
    )
    default_remarks = serializers.CharField(
        required=False, 
        allow_blank=True, 
        default="",
        help_text="Default remarks for all results"
    )
    
    # Options for creation
    include_inactive_students = serializers.BooleanField(
        default=False,
        help_text="Include inactive enrollments in result creation"
    )
    overwrite_existing = serializers.BooleanField(
        default=False,
        help_text="Overwrite existing results if they exist"
    )
    
    def validate_default_obtained_marks(self, value):
        """Validate default marks"""
        if value < 0:
            raise serializers.ValidationError("Obtained marks cannot be negative")
        return value


class ExamResultBulkPreviewSerializer(serializers.Serializer):
    """Serializer for bulk create preview"""
    
    def to_representation(self, instance):
        return {
            'exam': {
                'exam_id': instance['exam'].exam_id,
                'title': instance['exam'].title,
                'total_marks': str(instance['exam'].total_marks),
                'pass_marks': str(instance['exam'].pass_marks)
            },
            'batch': {
                'id': instance['batch'].id,
                'name': instance['batch'].name,
                'batch_id': instance['batch'].batch_id
            },
            'statistics': {
                'total_enrolled_students': instance['total_enrolled_students'],
                'active_enrollments': instance['active_enrollments'],
                'existing_results': instance['existing_results'],
                'results_to_create': instance['results_to_create']
            },
            'students_preview': [
                {
                    'student_id': student.id,
                    'student_identifier': student.student_id,
                    'name': student.user.get_full_name(),
                    'email': student.user.email,
                    'enrollment_date': student.batchenrollment_set.filter(
                        batch=instance['batch']
                    ).first().enrollment_date,
                    'has_existing_result': student.id in instance['existing_result_student_ids']
                }
                for student in instance['students_preview']
            ]
        }
    

class StudentExamSessionSerializer(serializers.Serializer):
    """Student exam session serializer"""
    id = serializers.IntegerField(read_only=True)
    session_id = serializers.CharField(read_only=True)
    started_at = serializers.DateTimeField(read_only=True)
    submitted_at = serializers.DateTimeField(read_only=True)
    status = serializers.CharField(read_only=True)
    time_spent_minutes = serializers.IntegerField(read_only=True)
    is_time_extended = serializers.BooleanField(read_only=True)
    extended_time_minutes = serializers.IntegerField(read_only=True)

    def to_representation(self, instance):
        data = {
            'id': instance.id,
            'session_id': instance.session_id,
            'started_at': instance.started_at,
            'submitted_at': instance.submitted_at,
            'last_activity_at': instance.last_activity_at,
            'status': instance.status,
            'status_display': instance.get_status_display(),
            'time_spent_minutes': instance.time_spent_minutes,
            'is_time_extended': instance.is_time_extended,
            'extended_time_minutes': instance.extended_time_minutes,
            'is_active': instance.is_active,
            'total_allowed_minutes': instance.total_allowed_minutes,
            'remaining_minutes': instance.remaining_minutes,
            'is_timeout': instance.is_timeout,
            'ip_address': instance.ip_address
        }

        # Add exam info
        if hasattr(instance, 'exam') and instance.exam:
            data['exam'] = {
                'id': instance.exam.id,
                'exam_id': instance.exam.exam_id,
                'title': instance.exam.title,
                'duration_minutes': instance.exam.duration_minutes,
                'total_marks': str(instance.exam.total_marks)
            }

        # Add student info
        if hasattr(instance, 'student') and instance.student:
            data['student'] = {
                'id': instance.student.id,
                'student_id': instance.student.student_id,
                'user': {
                    'full_name': instance.student.user.get_full_name()
                } if instance.student.user else None
            }

        # Add answer count if prefetched
        if hasattr(instance, 'answers'):
            data['total_answers'] = instance.answers.count()
            data['answered_questions'] = instance.answers.count()

        return data


class StudentAnswerSerializer(serializers.Serializer):
    """Student answer serializer"""
    id = serializers.IntegerField(read_only=True)
    text_answer = serializers.CharField(required=False, allow_blank=True)
    answered_at = serializers.DateTimeField(read_only=True)
    last_modified_at = serializers.DateTimeField(read_only=True)
    is_correct = serializers.BooleanField(read_only=True)
    awarded_marks = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    is_graded = serializers.BooleanField(read_only=True)
    grader_remarks = serializers.CharField(read_only=True)
    
    # Write-only fields for saving answers
    question_id = serializers.IntegerField(write_only=True, required=False)
    selected_option_id = serializers.IntegerField(write_only=True, required=False)

    def to_representation(self, instance):
        data = {
            'id': instance.id,
            'text_answer': instance.text_answer,
            'answered_at': instance.answered_at,
            'last_modified_at': instance.last_modified_at,
            'is_correct': instance.is_correct,
            'awarded_marks': str(instance.awarded_marks) if instance.awarded_marks else None,
            'is_graded': instance.is_graded,
            'grader_remarks': instance.grader_remarks
        }

        # Add question info
        if hasattr(instance, 'question') and instance.question:
            data['question'] = {
                'id': instance.question.id,
                'question_text': instance.question.question_text,
                'question_type': instance.question.question_type,
                'question_order': instance.question.question_order,
                'marks': str(instance.question.marks)
            }

        # Add selected option info
        if hasattr(instance, 'selected_option') and instance.selected_option:
            data['selected_option'] = {
                'id': instance.selected_option.id,
                'option_text': instance.selected_option.option_text,
                'is_correct': instance.selected_option.is_correct
            }

        # Add grader info
        if hasattr(instance, 'graded_by') and instance.graded_by:
            data['graded_by'] = {
                'id': instance.graded_by.id,
                'username': instance.graded_by.username,
                'full_name': instance.graded_by.get_full_name()
            }
            data['graded_at'] = instance.graded_at

        return data


class OnlineExamResultSerializer(ExamResultSerializer):
    """Online exam result serializer - extends ExamResultSerializer"""
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        # Add online-specific fields
        data.update({
            'auto_graded_marks': str(instance.auto_graded_marks),
            'manual_graded_marks': str(instance.manual_graded_marks),
            'total_questions': instance.total_questions,
            'total_questions_attempted': instance.total_questions_attempted,
            'completion_percentage': instance.completion_percentage,
            'is_auto_processed': instance.is_auto_processed,
            'is_manual_grading_complete': instance.is_manual_grading_complete,
            'requires_manual_grading': instance.requires_manual_grading
        })

        # Add session info
        if hasattr(instance, 'session') and instance.session:
            data['session'] = {
                'id': instance.session.id,
                'session_id': instance.session.session_id,
                'started_at': instance.session.started_at,
                'submitted_at': instance.session.submitted_at,
                'status': instance.session.status,
                'time_spent_minutes': instance.session.time_spent_minutes
            }

        return data


class OnlineExamResultSerializer_(serializers.Serializer):
    """Serializer for OnlineExamResult model"""
    result_id = serializers.CharField()
    auto_graded_marks = serializers.DecimalField(max_digits=6, decimal_places=2)
    manual_graded_marks = serializers.DecimalField(max_digits=6, decimal_places=2)
    total_questions_attempted = serializers.IntegerField()
    total_questions = serializers.IntegerField()
    is_auto_processed = serializers.BooleanField()
    is_manual_grading_complete = serializers.BooleanField()
    
    # Properties
    completion_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    requires_manual_grading = serializers.BooleanField()

    def to_representation(self, instance):
        # Get base exam result data
        base_data = ExamResultSerializer().to_representation(instance)
        
        # Add online-specific data
        online_data = {
            'auto_graded_marks': instance.auto_graded_marks,
            'manual_graded_marks': instance.manual_graded_marks,
            'total_questions_attempted': instance.total_questions_attempted,
            'total_questions': instance.total_questions,
            'is_auto_processed': instance.is_auto_processed,
            'is_manual_grading_complete': instance.is_manual_grading_complete,
            'completion_percentage': instance.completion_percentage,
            'requires_manual_grading': instance.requires_manual_grading,
            'session': {
                'session_id': instance.session.session_id,
                'started_at': instance.session.started_at,
                'submitted_at': instance.session.submitted_at,
                'time_spent_minutes': instance.session.time_spent_minutes,
                'status': instance.session.status,
            }
        }
        
        # Merge the data
        return {**base_data, **online_data}


class ExamAnalyticsSerializer(serializers.Serializer):
    """Serializer for exam analytics data"""
    
    def to_representation(self, instance):
        return {
            'total_students': instance.get('total_students', 0),
            'passed_students': instance.get('passed_students', 0),
            'failed_students': instance.get('failed_students', 0),
            'pass_percentage': instance.get('pass_percentage', 0),
            'average_marks': str(instance.get('average_marks', 0)) if instance.get('average_marks') else '0.00',
            'highest_marks': str(instance.get('highest_marks', 0)) if instance.get('highest_marks') else '0.00',
            'lowest_marks': str(instance.get('lowest_marks', 0)) if instance.get('lowest_marks') else '0.00',
            'grade_distribution': instance.get('grade_distribution', [])
        }


class ExamAnalyticsSerializer_(serializers.Serializer):
    """Serializer for exam analytics data"""
    total_students = serializers.IntegerField()
    results_submitted = serializers.IntegerField()
    pending_results = serializers.IntegerField()
    pass_count = serializers.IntegerField()
    fail_count = serializers.IntegerField()
    pass_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    average_marks = serializers.DecimalField(max_digits=6, decimal_places=2)
    highest_marks = serializers.DecimalField(max_digits=6, decimal_places=2)
    lowest_marks = serializers.DecimalField(max_digits=6, decimal_places=2)
    grade_distribution = serializers.DictField()

    def to_representation(self, instance):
        return {
            'total_students': instance['total_students'],
            'results_submitted': instance['results_submitted'],
            'pending_results': instance['pending_results'],
            'pass_count': instance['pass_count'],
            'fail_count': instance['fail_count'],
            'pass_percentage': instance['pass_percentage'],
            'average_marks': instance['average_marks'],
            'highest_marks': instance['highest_marks'],
            'lowest_marks': instance['lowest_marks'],
            'grade_distribution': instance['grade_distribution'],
        }


# Serializers for API requests
class ExamCreateSerializer(serializers.Serializer):
    """Serializer for creating exams"""
    batch_id = serializers.IntegerField()
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    subject = serializers.CharField()
    exam_date = serializers.DateTimeField()
    duration_minutes = serializers.IntegerField()
    total_marks = serializers.DecimalField(max_digits=6, decimal_places=2)
    pass_marks = serializers.DecimalField(max_digits=6, decimal_places=2)
    exam_type = serializers.ChoiceField(choices=EXAM_TYPE_CHOICES)


class ExamUpdateSerializer(serializers.Serializer):
    """Serializer for updating exams"""
    batch_id = serializers.IntegerField()
    title = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    subject = serializers.CharField()
    exam_date = serializers.DateTimeField(required=False)
    duration_minutes = serializers.IntegerField(required=False)
    total_marks = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    pass_marks = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    exam_type = serializers.ChoiceField(choices=EXAM_TYPE_CHOICES)


class ExamResultCreateSerializer(serializers.Serializer):
    """Serializer for creating exam results"""
    exam_id = serializers.CharField()
    student_id = serializers.IntegerField()
    batch_enrollment_id = serializers.IntegerField()
    obtained_marks = serializers.DecimalField(max_digits=6, decimal_places=2)
    was_present = serializers.BooleanField(default=True)
    remarks = serializers.CharField(required=False, allow_blank=True)


class StudentAnswerCreateSerializer(serializers.Serializer):
    """Serializer for creating/updating student answers"""
    question_id = serializers.IntegerField()
    selected_option_id = serializers.IntegerField(required=False)
    text_answer = serializers.CharField(required=False, allow_blank=True)


class StudentAnswerGradeSerializer(serializers.Serializer):
    """Serializer for grading student answers"""
    awarded_marks = serializers.DecimalField(max_digits=5, decimal_places=2)
    remarks = serializers.CharField(required=False, allow_blank=True)