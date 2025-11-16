import uuid
from datetime import datetime
from typing import Dict, Callable


class IDGenerator:
    """
    Centralized ID generation for exam-related entities.
    
    Generates unique IDs with format: {PREFIX}-{YEAR}-{UNIQUE_PART}
    where UNIQUE_PART is a 6-character uppercase string from UUID4.
    """
    
    # ID prefixes for different entity types
    _PREFIXES: Dict[str, str] = {
        'exam': 'EXM',
        'result': 'RES',
        'question': 'QST',
        'answer': 'ANS',
        'submission': 'SUB',
        'grade': 'GRD',
        'question_bank': 'QBK',
        'exam_schedule': 'ESC',
        'exam_session': 'ESS',
        'category': 'CAT',
    }
    
    @classmethod
    def _generate_base_id(cls, prefix: str, uuid_limit: int = 6) -> str:
        year = datetime.now().year
        unique_part = str(uuid.uuid4()).replace('-', '').upper()[:uuid_limit]
        return f'{prefix}{year}{unique_part}'
    
    @classmethod
    def generate_exam_id(cls) -> str:
        """Generate unique exam ID"""
        return cls._generate_base_id(cls._PREFIXES['exam'], uuid_limit=16)
    
    @classmethod
    def generate_result_id(cls) -> str:
        """Generate unique result ID"""
        return cls._generate_base_id(cls._PREFIXES['result'], uuid_limit=16)

    @classmethod
    def generate_question_id(cls) -> str:
        """Generate unique question ID"""
        return cls._generate_base_id(cls._PREFIXES['question'], uuid_limit=16)

    @classmethod
    def generate_answer_id(cls) -> str:
        """Generate unique answer ID"""
        return cls._generate_base_id(cls._PREFIXES['answer'], uuid_limit=16)
    
    @classmethod
    def generate_submission_id(cls) -> str:
        """Generate unique submission ID"""
        return cls._generate_base_id(cls._PREFIXES['submission'], uuid_limit=16)

    @classmethod
    def generate_grade_id(cls) -> str:
        """Generate unique grade ID"""
        return cls._generate_base_id(cls._PREFIXES['grade'])
    

    @classmethod
    def generate_question_bank_id(cls) -> str:
        """Generate unique question bank ID"""
        return cls._generate_base_id(cls._PREFIXES['question_bank'], uuid_limit=16)

    @classmethod
    def generate_category_id(cls) -> str:
        """Generate unique category ID"""
        return cls._generate_base_id(cls._PREFIXES['category'])

    @classmethod
    def generate_custom_id(cls, entity_type: str) -> str:
        """
        Generate ID for custom entity type.
        
        Args:
            entity_type: The type of entity (must exist in _PREFIXES)
            
        Returns:
            Generated ID string
            
        Raises:
            ValueError: If entity_type is not supported
        """
        if entity_type not in cls._PREFIXES:
            raise ValueError(f'Unsupported entity type: {entity_type}')
        
        return cls._generate_base_id(cls._PREFIXES[entity_type])
    
    @classmethod
    def get_supported_types(cls) -> list[str]:
        """Get list of supported entity types"""
        return list(cls._PREFIXES.keys())


# New way (recommended)
exam_id = IDGenerator.generate_exam_id()  # EXM-2025-A1B2C3
result_id = IDGenerator.generate_result_id()  # RES-2025-D4E5F6
answer_id = IDGenerator.generate_answer_id()  # ANS-2025-G7H8I9

# Custom entity type
submission_id = IDGenerator.generate_custom_id('submission')  # SUB-2025-J1K2L3

# Get supported types
types = IDGenerator.get_supported_types()  # ['exam', 'result', 'question', ...]