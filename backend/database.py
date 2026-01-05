"""
Database operations using JSON files.

Why JSON files for this project?
- No database setup required (beginner-friendly)
- Easy to inspect and debug (just open the JSON file)
- Portable (works on any OS)
- Good for learning and small projects

Limitations:
- Not suitable for production or concurrent users
- No transactions or ACID guarantees
- Performance degrades with large datasets
- File locking is basic

Migration path:
- SQLite: Easy drop-in replacement, single file
- PostgreSQL: Production-ready, handles concurrency
- MongoDB: If you prefer document structure
"""

import json
import os
from typing import List, Optional
from pathlib import Path
import threading
from models import User, Quiz, QuizResult

# Data directory configuration
# Use path relative to this file so it works regardless of current working directory
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# File paths
USERS_FILE = DATA_DIR / "users.json"
QUIZZES_FILE = DATA_DIR / "quizzes.json"
RESULTS_FILE = DATA_DIR / "results.json"

# Thread locks for file access
# Prevents race conditions when multiple requests access same file
users_lock = threading.Lock()
quizzes_lock = threading.Lock()
results_lock = threading.Lock()


class Database:
    """
    Simple JSON file-based database.
    
    Features:
    - Thread-safe file operations with locks
    - Atomic writes (temp file + rename)
    - Automatic initialization with default data
    - Sample admin user and quiz for testing
    """
    
    def __init__(self):
        """
        Initialize database files and create default data
        Called once when FastAPI starts
        """
        self._init_file(USERS_FILE, [])
        self._init_file(QUIZZES_FILE, [])
        self._init_file(RESULTS_FILE, [])
        self._create_default_admin()
    
    def _init_file(self, filepath: Path, default_data: list):
        """Create file with default data if it doesn't exist"""
        if not filepath.exists():
            with open(filepath, 'w') as f:
                json.dump(default_data, f, indent=2)
    
    def _read_json(self, filepath: Path, lock: threading.Lock) -> list:
        """
        Safely read JSON file with lock.
        
        Thread safety: Lock ensures only one thread reads at a time
        Error handling: Returns empty list if file is corrupted
        """
        with lock:
            try:
                with open(filepath, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return []
    
    def _write_json(self, filepath: Path, data: list, lock: threading.Lock):
        """
        Safely write JSON file with lock and atomic operation.
        
        Atomic write process:
        1. Write to temporary file
        2. Flush to disk
        3. Rename temp file to target file (atomic on all OS)
        
        Why atomic?
        - If process crashes during write, original file is intact
        - No partial/corrupted data
        - Other processes see old or new data, never partial
        """
        with lock:
            # Write to temporary file first
            temp_file = filepath.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Atomic rename (works on Windows, Linux, Mac)
            temp_file.replace(filepath)
    
    def _create_default_admin(self):
        """
        Create default admin user if none exists.
        Also creates sample quiz for testing.
        """
        from auth import hash_password
        import uuid
        
        users = self._read_json(USERS_FILE, users_lock)
        
        # Check if admin already exists
        if not any(u['email'] == 'admin@example.com' for u in users):
            admin = {
                "id": "admin-001",
                "name": "Admin User",
                "email": "admin@example.com",
                "password_hash": hash_password("Admin123!"),  # Default password
                "role": "admin"
            }
            users.append(admin)
            self._write_json(USERS_FILE, users, users_lock)
            
            # Create sample quiz
            self._create_sample_quiz()
    
    def _create_sample_quiz(self):
        """Create a sample quiz for testing"""
        import uuid
        
        sample_quiz = {
            "id": str(uuid.uuid4()),
            "title": "Python Basics Quiz",
            "description": "Test your knowledge of Python fundamentals",
            "time_limit_minutes": 10,
            "questions": [
                {
                    "id": str(uuid.uuid4()),
                    "text": "What is the output of print(type([]))?",
                    "options": [
                        "<class 'list'>",
                        "<class 'dict'>",
                        "<class 'tuple'>",
                        "<class 'set'>"
                    ],
                    "correct_option_index": 0
                },
                {
                    "id": str(uuid.uuid4()),
                    "text": "Which keyword is used to define a function in Python?",
                    "options": [
                        "function",
                        "def",
                        "func",
                        "define"
                    ],
                    "correct_option_index": 1
                },
                {
                    "id": str(uuid.uuid4()),
                    "text": "What does the 'self' parameter represent in Python classes?",
                    "options": [
                        "The class itself",
                        "The instance of the class",
                        "A static variable",
                        "The parent class"
                    ],
                    "correct_option_index": 1
                },
                {
                    "id": str(uuid.uuid4()),
                    "text": "Which data structure is mutable in Python?",
                    "options": [
                        "tuple",
                        "string",
                        "list",
                        "int"
                    ],
                    "correct_option_index": 2
                },
                {
                    "id": str(uuid.uuid4()),
                    "text": "What is the correct way to create a dictionary?",
                    "options": [
                        "dict = []",
                        "dict = ()",
                        "dict = {}",
                        "dict = <>"
                    ],
                    "correct_option_index": 2
                }
            ]
        }
        
        quizzes = self._read_json(QUIZZES_FILE, quizzes_lock)
        quizzes.append(sample_quiz)
        self._write_json(QUIZZES_FILE, quizzes, quizzes_lock)
    
    # ========================================================================
    # USER OPERATIONS
    # ========================================================================
    
    def create_user(self, user: User):
        """Add new user to database"""
        users = self._read_json(USERS_FILE, users_lock)
        users.append(user.dict())
        self._write_json(USERS_FILE, users, users_lock)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Find user by email (for login)"""
        users = self._read_json(USERS_FILE, users_lock)
        user_data = next((u for u in users if u['email'] == email), None)
        return User(**user_data) if user_data else None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Find user by ID (for JWT verification)"""
        users = self._read_json(USERS_FILE, users_lock)
        user_data = next((u for u in users if u['id'] == user_id), None)
        return User(**user_data) if user_data else None
    
    # ========================================================================
    # QUIZ OPERATIONS
    # ========================================================================
    
    def create_quiz(self, quiz: Quiz):
        """Add new quiz to database"""
        quizzes = self._read_json(QUIZZES_FILE, quizzes_lock)
        quizzes.append(quiz.dict())
        self._write_json(QUIZZES_FILE, quizzes, quizzes_lock)
    
    def get_all_quizzes(self) -> List[Quiz]:
        """Get all quizzes (for listing)"""
        quizzes = self._read_json(QUIZZES_FILE, quizzes_lock)
        return [Quiz(**q) for q in quizzes]
    
    def get_quiz_by_id(self, quiz_id: str) -> Optional[Quiz]:
        """Find quiz by ID"""
        quizzes = self._read_json(QUIZZES_FILE, quizzes_lock)
        quiz_data = next((q for q in quizzes if q['id'] == quiz_id), None)
        return Quiz(**quiz_data) if quiz_data else None
    
    def update_quiz(self, quiz: Quiz):
        """
        Update existing quiz.
        Replaces entire quiz object (no partial updates)
        """
        quizzes = self._read_json(QUIZZES_FILE, quizzes_lock)
        updated_quizzes = [
            quiz.dict() if q['id'] == quiz.id else q
            for q in quizzes
        ]
        self._write_json(QUIZZES_FILE, updated_quizzes, quizzes_lock)
    
    def delete_quiz(self, quiz_id: str):
        """Delete quiz by ID"""
        quizzes = self._read_json(QUIZZES_FILE, quizzes_lock)
        filtered_quizzes = [q for q in quizzes if q['id'] != quiz_id]
        self._write_json(QUIZZES_FILE, filtered_quizzes, quizzes_lock)
    
    # ========================================================================
    # RESULT OPERATIONS
    # ========================================================================
    
    def create_result(self, result: QuizResult):
        """
        Add new result to database.
        Called when student starts a quiz (with empty answers)
        """
        results = self._read_json(RESULTS_FILE, results_lock)
        results.append(result.dict())
        self._write_json(RESULTS_FILE, results, results_lock)
    
    def get_result_by_id(self, result_id: str) -> Optional[QuizResult]:
        """Find result by ID (attempt_id)"""
        results = self._read_json(RESULTS_FILE, results_lock)
        result_data = next((r for r in results if r['id'] == result_id), None)
        return QuizResult(**result_data) if result_data else None
    
    def update_result(self, result: QuizResult):
        """
        Update existing result.
        Called when student submits quiz (adds answers and score)
        """
        results = self._read_json(RESULTS_FILE, results_lock)
        updated_results = [
            result.dict() if r['id'] == result.id else r
            for r in results
        ]
        self._write_json(RESULTS_FILE, updated_results, results_lock)
    
    def get_results_by_quiz(self, quiz_id: str) -> List[QuizResult]:
        """Get all results for a specific quiz (for admin view)"""
        results = self._read_json(RESULTS_FILE, results_lock)
        return [QuizResult(**r) for r in results if r['quiz_id'] == quiz_id]


# ============================================================================
# Migration Guide to Real Database:
#
# SQLite (easiest):
# 1. Install: pip install sqlalchemy aiosqlite
# 2. Define models with SQLAlchemy ORM
# 3. Replace file operations with database queries
# 4. Single file database (data/quiz_app.db)
#
# PostgreSQL (production):
# 1. Install: pip install sqlalchemy asyncpg
# 2. Set up PostgreSQL server
# 3. Create database and tables
# 4. Update connection string in environment variable
# 5. Use connection pooling
#
# MongoDB (document-oriented):
# 1. Install: pip install motor
# 2. Set up MongoDB server
# 3. Replace operations with MongoDB queries
# 4. Schema is flexible (similar to JSON)
#
# All options work well with FastAPI's async capabilities!
# ============================================================================