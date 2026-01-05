# ============================================================================
# FILE: main.py
# Main FastAPI application - Entry point for backend server
# ============================================================================

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from datetime import datetime, timedelta, timezone
import uuid

from models import (
    UserSignup, UserLogin, User, TokenResponse,
    QuizCreate, Quiz, QuizDetail, QuestionResponse,
    QuizStart, QuizSubmit, QuizResult, ResultDetail
)
from auth import hash_password, verify_password, create_access_token, verify_token
from database import Database

# Initialize FastAPI app
app = FastAPI(title="Quiz Application API", version="1.0.0")

# Configure CORS - allows frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",
        "http://localhost:5178",
        "http://localhost:5179"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
db = Database()

# Security scheme for JWT authentication
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Extract and validate JWT token, return current user"""
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user = db.get_user_by_id(payload["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Ensure current user has admin role"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/api/auth/signup", response_model=TokenResponse)
async def signup(user_data: UserSignup):
    """
    Register new user (student or admin)
    - Checks email uniqueness
    - Hashes password with bcrypt
    - Returns JWT token for immediate login
    """
    print(f"Signup attempt for email: {user_data.email}")  # Debug log
    try:
        if db.get_user_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        user = User(
            id=str(uuid.uuid4()),
            name=user_data.name,
            email=user_data.email,
            password_hash=hash_password(user_data.password),
            role=user_data.role
        )
        
        print(f"Creating new user with ID: {user.id}")  # Debug log
        db.create_user(user)
        token = create_access_token({"user_id": user.id, "role": user.role})
        print("User created successfully")  # Debug log
        
        return TokenResponse(access_token=token, user=user)
    except Exception as e:
        print(f"Error during signup: {str(e)}")  # Debug log
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signup failed: {str(e)}"
        )


@app.post("/api/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """
    Authenticate user and return JWT token
    - Validates email and password
    - Returns token with user info
    """
    user = db.get_user_by_email(credentials.email)
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    token = create_access_token({"user_id": user.id, "role": user.role})
    return TokenResponse(access_token=token, user=user)


# ============================================================================
# QUIZ ENDPOINTS
# ============================================================================

@app.get("/api/quizzes", response_model=List[Quiz])
async def list_quizzes():
    """Get all quizzes (public endpoint)"""
    return db.get_all_quizzes()


@app.get("/api/quizzes/{quiz_id}", response_model=QuizDetail)
async def get_quiz(quiz_id: str, current_user: User = Depends(get_current_user)):
    """
    Get quiz details
    - Students see questions without correct answers
    - Admins see complete quiz with answers
    """
    quiz = db.get_quiz_by_id(quiz_id)
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # Hide correct answers for students
    if current_user.role == "student":
        questions = [
            QuestionResponse(
                id=q.id,
                text=q.text,
                options=q.options,
                correct_option_index=None
            )
            for q in quiz.questions
        ]
    else:
        questions = [
            QuestionResponse(
                id=q.id,
                text=q.text,
                options=q.options,
                correct_option_index=q.correct_option_index
            )
            for q in quiz.questions
        ]
    
    return QuizDetail(
        id=quiz.id,
        title=quiz.title,
        description=quiz.description,
        time_limit_minutes=quiz.time_limit_minutes,
        questions=questions
    )


@app.post("/api/quizzes", response_model=Quiz, status_code=status.HTTP_201_CREATED)
async def create_quiz(quiz_data: QuizCreate, admin: User = Depends(require_admin)):
    """Create new quiz (admin only)"""
    quiz = Quiz(
        id=str(uuid.uuid4()),
        title=quiz_data.title,
        description=quiz_data.description,
        time_limit_minutes=quiz_data.time_limit_minutes,
        questions=quiz_data.questions
    )
    
    db.create_quiz(quiz)
    return quiz


@app.put("/api/quizzes/{quiz_id}", response_model=Quiz)
async def update_quiz(
    quiz_id: str,
    quiz_data: QuizCreate,
    admin: User = Depends(require_admin)
):
    """Update existing quiz (admin only)"""
    existing_quiz = db.get_quiz_by_id(quiz_id)
    
    if not existing_quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    updated_quiz = Quiz(
        id=quiz_id,
        title=quiz_data.title,
        description=quiz_data.description,
        time_limit_minutes=quiz_data.time_limit_minutes,
        questions=quiz_data.questions
    )
    
    db.update_quiz(updated_quiz)
    return updated_quiz


@app.delete("/api/quizzes/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quiz(quiz_id: str, admin: User = Depends(require_admin)):
    """Delete quiz (admin only)"""
    if not db.get_quiz_by_id(quiz_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    db.delete_quiz(quiz_id)


# ============================================================================
# QUIZ ATTEMPT ENDPOINTS
# ============================================================================

@app.post("/api/quizzes/{quiz_id}/start", response_model=QuizStart)
async def start_quiz(quiz_id: str, current_user: User = Depends(get_current_user)):
    """
    Start quiz attempt (students only)
    - Creates attempt record with start time
    - Returns attempt_id for submission
    """
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can take quizzes"
        )
    
    quiz = db.get_quiz_by_id(quiz_id)
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # Check for any prior attempts by this user
    existing_attempts = db.get_results_by_quiz(quiz_id)
    # If a completed attempt exists, block further attempts
    for attempt in existing_attempts:
        if attempt.user_id == current_user.id and attempt.end_time is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already completed this quiz. Multiple attempts are not allowed."
            )

    # Check for existing unfinished attempts by this user
    for attempt in existing_attempts:
        if attempt.user_id == current_user.id and attempt.end_time is None:
            # Parse stored start time (support both naive ISO and trailing 'Z')
            raw_start = attempt.start_time
            try:
                if raw_start.endswith('Z'):
                    stored_start = datetime.fromisoformat(raw_start.replace('Z', '+00:00'))
                else:
                    stored_start = datetime.fromisoformat(raw_start)
                # Normalize to aware UTC
                if stored_start.tzinfo is None:
                    stored_start = stored_start.replace(tzinfo=timezone.utc)
            except ValueError:
                # If parsing fails, treat as expired and continue to create a new attempt
                stored_start = None

            if stored_start:
                now_utc = datetime.now(timezone.utc)
                elapsed_minutes = (now_utc - stored_start).total_seconds() / 60
                # If attempt is still within allowed time window (including 30s grace), return it
                if elapsed_minutes <= quiz.time_limit_minutes + 0.5:
                    # Debug log: returning existing unfinished attempt
                    print(f"[DEBUG] Returning existing attempt {attempt.id} for user {current_user.id}. elapsed_minutes={elapsed_minutes:.2f}")
                    # Always return ISO string with 'Z' suffix for UTC consistency
                    start_time_iso_z = stored_start.isoformat()
                    if not start_time_iso_z.endswith('Z') and '+' not in start_time_iso_z:
                        start_time_iso_z = start_time_iso_z + 'Z'
                    return QuizStart(
                        attempt_id=attempt.id,
                        start_time=start_time_iso_z,
                        time_limit_minutes=quiz.time_limit_minutes
                    )
                else:
                    # Expired attempt: mark it as ended to avoid resuming an expired session
                    end_dt = stored_start + timedelta(minutes=quiz.time_limit_minutes)
                    # Ensure ISO Z suffix
                    attempt.end_time = end_dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
                    db.update_result(attempt)
                    print(f"[DEBUG] Marked expired attempt {attempt.id} as ended (user {current_user.id}). elapsed_minutes={elapsed_minutes:.2f}")
                    # continue to create a fresh attempt

    # Create new attempt only if no unfinished attempt exists
    attempt_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)
    
    # Store timestamps as UTC ISO strings with explicit 'Z' suffix so clients
    # can reliably parse them as UTC. We append 'Z' to the naive UTC isoformat.
    start_iso_z = start_time.isoformat().replace('+00:00', 'Z')

    result = QuizResult(
        id=attempt_id,
        quiz_id=quiz_id,
        user_id=current_user.id,
        start_time=start_iso_z,
        end_time=None,
        answers=[],
        score=0
    )
    
    db.create_result(result)
    
    return QuizStart(
        attempt_id=attempt_id,
        start_time=start_iso_z,
        time_limit_minutes=quiz.time_limit_minutes
    )


@app.post("/api/quizzes/{quiz_id}/submit", response_model=ResultDetail)
async def submit_quiz(
    quiz_id: str,
    submission: QuizSubmit,
    current_user: User = Depends(get_current_user)
):
    """
    Submit quiz answers
    - Validates time window (with 30 second grace period)
    - Calculates score
    - Returns detailed results with per-question feedback
    """
    quiz = db.get_quiz_by_id(quiz_id)
    result = db.get_result_by_id(submission.attempt_id)
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attempt not found"
        )
    
    if result.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to submit this attempt"
        )
    
    # Validate time window
    # Accept either a plain ISO string (no timezone) or a trailing 'Z'. If the
    # stored time ends with 'Z' convert it to an explicit +00:00 offset so
    # datetime.fromisoformat can parse it across Python versions.
    try:
        raw_start = result.start_time
        if raw_start.endswith('Z'):
            # replace trailing Z with +00:00 for ISO offset parsing
            start_time = datetime.fromisoformat(raw_start.replace('Z', '+00:00'))
        else:
            start_time = datetime.fromisoformat(raw_start)
        # Normalize to aware UTC for arithmetic
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        end_time = datetime.now(timezone.utc)
        elapsed_minutes = (end_time - start_time).total_seconds() / 60
        
        if elapsed_minutes > quiz.time_limit_minutes + 0.5:  # 30 second grace
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Time limit exceeded. Quiz must be submitted within {quiz.time_limit_minutes} minutes. Elapsed time: {round(elapsed_minutes, 1)} minutes"
            )
    except ValueError as e:
        # Handle timestamp parsing errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid timestamp format: {str(e)}"
        )
    
    # Calculate score and build question results
    correct_count = 0
    question_results = []
    
    for answer in submission.answers:
        question = next((q for q in quiz.questions if q.id == answer.question_id), None)
        if question:
            is_correct = answer.chosen_index == question.correct_option_index
            if is_correct:
                correct_count += 1
            
            question_results.append({
                "question_id": answer.question_id,
                "question_text": question.text,
                "chosen_index": answer.chosen_index,
                "correct_index": question.correct_option_index,
                "is_correct": is_correct
            })
    
    score = (correct_count / len(quiz.questions)) * 100 if quiz.questions else 0
    
    # Update result in database
    # Store end_time also with explicit 'Z' suffix
    result.end_time = end_time.isoformat().replace('+00:00', 'Z')
    result.answers = [a.dict() for a in submission.answers]
    result.score = round(score, 2)
    
    db.update_result(result)
    
    return ResultDetail(
        id=result.id,
        quiz_id=quiz_id,
        quiz_title=quiz.title,
        user_id=current_user.id,
        user_name=current_user.name,
        start_time=result.start_time,
        end_time=result.end_time,
        score=result.score,
        total_questions=len(quiz.questions),
        correct_answers=correct_count,
        question_results=question_results
    )


@app.get("/api/quizzes/{quiz_id}/results", response_model=List[ResultDetail])
async def get_quiz_results(quiz_id: str, admin: User = Depends(require_admin)):
    """
    Get all student results for a quiz (admin only)
    - Returns completed attempts with detailed breakdown
    """
    quiz = db.get_quiz_by_id(quiz_id)
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    results = db.get_results_by_quiz(quiz_id)
    detailed_results = []
    
    for result in results:
        if not result.end_time:  # Skip incomplete attempts
            continue
        
        user = db.get_user_by_id(result.user_id)
        
        # Reconstruct question results
        question_results = []
        for answer in result.answers:
            question = next((q for q in quiz.questions if q.id == answer["question_id"]), None)
            if question:
                question_results.append({
                    "question_id": answer["question_id"],
                    "question_text": question.text,
                    "chosen_index": answer["chosen_index"],
                    "correct_index": question.correct_option_index,
                    "is_correct": answer["chosen_index"] == question.correct_option_index
                })
        
        detailed_results.append(ResultDetail(
            id=result.id,
            quiz_id=quiz_id,
            quiz_title=quiz.title,
            user_id=result.user_id,
            user_name=user.name if user else "Unknown",
            start_time=result.start_time,
            end_time=result.end_time,
            score=result.score,
            total_questions=len(quiz.questions),
            correct_answers=sum(1 for qr in question_results if qr["is_correct"]),
            question_results=question_results
        ))
    
    return detailed_results


@app.get("/api/quizzes/{quiz_id}/my-result", response_model=ResultDetail)
async def get_my_quiz_result(quiz_id: str, current_user: User = Depends(get_current_user)):
    """
    Get the current student's completed attempt for a quiz.
    Returns the most recent completed attempt with detailed breakdown.
    """
    quiz = db.get_quiz_by_id(quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )

    # Filter to completed attempts by this user
    attempts = [r for r in db.get_results_by_quiz(quiz_id) if r.user_id == current_user.id and r.end_time]
    if not attempts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No completed attempt found for this user"
        )

    # Pick the latest by end_time
    latest = sorted(
        attempts,
        key=lambda r: r.end_time or "",
        reverse=True
    )[0]

    # Build question results
    question_results = []
    for answer in latest.answers:
        question = next((q for q in quiz.questions if q.id == answer["question_id"]), None)
        if question:
            question_results.append({
                "question_id": answer["question_id"],
                "question_text": question.text,
                "chosen_index": answer["chosen_index"],
                "correct_index": question.correct_option_index,
                "is_correct": answer["chosen_index"] == question.correct_option_index
            })

    user = db.get_user_by_id(latest.user_id)
    return ResultDetail(
        id=latest.id,
        quiz_id=quiz_id,
        quiz_title=quiz.title,
        user_id=latest.user_id,
        user_name=user.name if user else "Unknown",
        start_time=latest.start_time,
        end_time=latest.end_time,
        score=latest.score,
        total_questions=len(quiz.questions),
        correct_answers=sum(1 for qr in question_results if qr["is_correct"]),
        question_results=question_results
    )


@app.get("/api/results/{attempt_id}", response_model=ResultDetail)
async def get_result_by_attempt(attempt_id: str, current_user: User = Depends(get_current_user)):
    """
    Get a specific attempt's detailed results by attempt_id.
    - Students can only access their own attempts
    - Admins can access any attempt
    """
    result = db.get_result_by_id(attempt_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attempt not found"
        )

    # Authorization: student must own the attempt
    if current_user.role != "admin" and result.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this attempt"
        )

    quiz = db.get_quiz_by_id(result.quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )

    question_results = []
    for answer in result.answers:
        question = next((q for q in quiz.questions if q.id == answer["question_id"]), None)
        if question:
            question_results.append({
                "question_id": answer["question_id"],
                "question_text": question.text,
                "chosen_index": answer["chosen_index"],
                "correct_index": question.correct_option_index,
                "is_correct": answer["chosen_index"] == question.correct_option_index
            })

    user = db.get_user_by_id(result.user_id)
    return ResultDetail(
        id=result.id,
        quiz_id=result.quiz_id,
        quiz_title=quiz.title,
        user_id=result.user_id,
        user_name=user.name if user else "Unknown",
        start_time=result.start_time,
        end_time=result.end_time,
        score=result.score,
        total_questions=len(quiz.questions),
        correct_answers=sum(1 for qr in question_results if qr["is_correct"]),
        question_results=question_results
    )


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "Quiz Application API"}
   

# ============================================================================
# Run with: uvicorn main:app --reload --port 8000
# ============================================================================