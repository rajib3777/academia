from datetime import datetime
from django.db import transaction


def generate_academy_id(prefix: str = 'AID') -> str:
    """
    Generate a unique academy ID with the given prefix.

    Args:
        prefix (str): Prefix for the academy ID. Default is 'AID'.

    Returns:
        str: Generated academy ID.
    """
    from academy.models import Academy
    
    current_year = datetime.now().year
    year_prefix = f'{prefix}-{current_year}'
    
    with transaction.atomic():
        academies = Academy.objects.filter(
            academy_id__startswith=f'{year_prefix}-'
        ).exclude(academy_id__isnull=True).values_list('academy_id', flat=True)
        
        max_number = 0
        for academy_id in academies:
            try:
                # Extract number part after year (e.g., 'AID-2025-001' -> '001')
                parts = academy_id.split('-')
                if len(parts) >= 3 and parts[2].isdigit():
                    max_number = max(max_number, int(parts[2]))
            except (IndexError, ValueError):
                continue
                
        next_number = max_number + 1
        return f'{year_prefix}-{next_number:04d}'  # 4-digit zero-padded


def generate_course_id(prefix: str = 'CID') -> str:
    """
    Generate a unique course ID with the given prefix using UUID.

    Args:
        prefix (str): Prefix for the course ID. Default is 'CID'.

    Returns:
        str: Generated course ID.
    """
    from academy.models import Course
    
    current_year = datetime.now().year
    year_prefix = f'{prefix}-{current_year}'
    
    with transaction.atomic():
        courses = Course.objects.filter(
            course_id__startswith=f'{year_prefix}-'
        ).exclude(course_id__isnull=True).values_list('course_id', flat=True)
        
        max_number = 0
        for course_id in courses:
            try:
                parts = course_id.split('-')
                if len(parts) >= 3 and parts[2].isdigit():
                    max_number = max(max_number, int(parts[2]))
            except (IndexError, ValueError):
                continue
        next_number = max_number + 1
        return f'{year_prefix}-{next_number:04d}'


def generate_batch_id(prefix: str = 'BID') -> str:
    """
    Generate a unique batch ID with the given prefix.

    Args:
        prefix (str): Prefix for the batch ID. Default is 'BID'.

    Returns:
        str: Generated batch ID.
    """
    from academy.models import Batch
    
    current_year = datetime.now().year
    year_prefix = f'{prefix}-{current_year}'
    
    with transaction.atomic():
        batches = Batch.objects.filter(
            batch_id__startswith=f'{year_prefix}-'
        ).exclude(batch_id__isnull=True).values_list('batch_id', flat=True)
        
        max_number = 0
        for batch_id in batches:
            try:
                parts = batch_id.split('-')
                if len(parts) >= 3 and parts[2].isdigit():
                    max_number = max(max_number, int(parts[2]))
            except (IndexError, ValueError):
                continue
        next_number = max_number + 1
        return f'{year_prefix}-{next_number:04d}'
