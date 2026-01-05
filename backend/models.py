"""
Pydantic models for request/response validation.
These define the structure of all data flowing through the API.

Why Pydantic?
- Automatic validation of incoming data
- Clear error messages for invalid input
- Type safety and autocompletion
- Automatic API documentation
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional
from enum import Enum
import uuid


class UserRole(str, Enum):
    """User role enumeration - only two roles allowed"""
    student = "student"
    admin = "admin"


# ============================================================================
# USER MODELS
# ============================================================================

class UserSignup(BaseModel):
    """Request model for user registration"""
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr  # Automatically validates email format
    password: str = Field(..., min_length=6)
    role: UserRole
    
    @validator('password')
    def validate_password(cls, v):
        """
        Custom password validation
        Requirement: At least 6 characters
        For production: add complexity requirements (uppercase, numbers, symbols)
        """
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v


class UserLogin(BaseModel):
    """Request model for user login"""
    email: EmailStr
    password: str


class User(BaseModel):
    """
    User model stored in database
    Note: password_hash is never sent to frontend
    """
    id: str
    name: str
    email: EmailStr
    password_hash: str
    role: UserRole


class TokenResponse(BaseModel):
    """
    Response model for authentication endpoints
    Returns JWT token and user info (without password)
    """
    access_token: str
    user: User


# ============================================================================
# QUIZ MODELS
# ============================================================================

class Question(BaseModel):
    """
    Quiz question model
    - Supports 2-6 options
    - correct_option_index is 0-based (0 = first option)
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str = Field(..., min_length=5)
    options: List[str] = Field(..., min_items=2, max_items=6)
    correct_option_index: int = Field(..., ge=0)
    
    @validator('correct_option_index')
    def validate_correct_option(cls, v, values):
        """Ensure correct_option_index is within options range"""
        if 'options' in values and v >= len(values['options']):
            raise ValueError('correct_option_index must be valid option index')
        return v


class QuizCreate(BaseModel):
    """Request model for creating/updating quizzes"""
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., max_length=1000)
    time_limit_minutes: int = Field(..., gt=0, le=180)  # 1-180 minutes
    questions: List[Question] = Field(..., min_items=1)


class Quiz(QuizCreate):
    """Quiz model stored in database (includes ID)"""
    id: str


class QuestionResponse(BaseModel):
    """
    Question model for API responses
    correct_option_index is None for students, visible for admins
    """
    id: str
    text: str
    options: List[str]
    correct_option_index: Optional[int] = None


class QuizDetail(BaseModel):
    """Detailed quiz response with questions"""
    id: str
    title: str
    description: str
    time_limit_minutes: int
    questions: List[QuestionResponse]


# ============================================================================
# QUIZ ATTEMPT MODELS
# ============================================================================

class QuizStart(BaseModel):
    """
    Response when starting a quiz
    Frontend uses this to:
    - Track the attempt
    - Start countdown timer
    - Submit with correct attempt_id
    """
    attempt_id: str
    start_time: str  # ISO format: "2024-01-15T10:30:00"
    time_limit_minutes: int


class Answer(BaseModel):
    """Single answer in quiz submission"""
    question_id: str
    chosen_index: int = Field(..., ge=0)


class QuizSubmit(BaseModel):
    """
    Request model for submitting quiz answers
    Student sends:
    - attempt_id (from /start endpoint)
    - answers array with their choices
    """
    attempt_id: str
    answers: List[Answer]


class QuizResult(BaseModel):
    """
    Quiz result stored in database
    Tracks complete attempt from start to submission
    """
    id: str  # Same as attempt_id
    quiz_id: str
    user_id: str
    start_time: str
    end_time: Optional[str]
    answers: List[dict]
    score: float


class ResultDetail(BaseModel):
    """
    Detailed result response
    Includes per-question breakdown for feedback
    """
    id: str
    quiz_id: str
    quiz_title: str
    user_id: str
    user_name: str
    start_time: str
    end_time: Optional[str]
    score: float
    total_questions: int
    correct_answers: int
    question_results: List[dict]  # Each item: {question_id, question_text, chosen_index, correct_index, is_correct}


# ============================================================================
# Example Usage:
# 
# Creating a question:
# q = Question(
#     text="What is 2 + 2?",
#     options=["3", "4", "5", "6"],
#     correct_option_index=1  # "4" is at index 1
# )
#
# The ID is automatically generated via default_factory
# ============================================================================